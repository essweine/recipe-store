import requests, json, re
from requests import HTTPError, Timeout
from urlparse import urljoin
import logging, time
from datetime import datetime
from lxml import html

class Collector(object):
    """
    Library for collecting annotated recipes: http://schema.org/Recipe
    """

    def __init__(self, collection, links, site_profile,
                 store_fields, required_fields,
                 link_depth = 0, pause = 10, timeout = 60, max_retries = 2):

        """
        Store or update the specified fields from recipes in a list of links, each request, 
        ignoring recipes if any required fields are missing, and optionally crawls a site to
        the specified depth based on the parameters in the site profile.
        """

        self.logger = logging.getLogger(__name__)
        self.collection = collection

        # General options
        self.store_fields = store_fields
        self.required_fields = required_fields
        self.links = links
        self.link_depth = link_depth
        self.link_queue = [ ]

        # Network options
        self.pause = pause
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_interval = 60

        # Site specific parameters

        self.base_url = site_profile.get("base_url", None)
        if self.base_url is None:
            raise Exception("You must specify a base url!")
        self.link_prefix = site_profile.get("link_prefix", "")

        extract_method = site_profile.get("extract_method", None)
        if extract_method == "microdata":
            self.extract = self.extract_from_html
            self.scope = "//*[@itemtype='http://schema.org/Recipe']"
            self.attribute = "itemprop"
        elif extract_method == "RDFa":
            self.extract = self.extract_from_html
            self.scope = "//*[@typeof='Recipe']"
            self.attribute = "property"
        elif extract_method == "json-ld":
            self.extract = self.extract_from_json_ld
        else:
            raise Exception("Invalid extraction method!  Valid methods: json-ld, microdata, RDFa")

    def process_links(self):
        """Process the provided list of links, collecting unseen recipes, and other links to follow,
        where applicable; manages the link queue to stop collection at the specified depth."""

        self.logger.info("Current depth is %d, list contains %d items" % 
                         (self.link_depth, len(self.links)))

        for url in self.links:

            duplicate = True if self.collection.find_one({ "url": url }) else False
            if duplicate and self.link_depth == 0:
                self.logger.info("Skipping url: %s" % url)
                continue

            try:
                data = self.get_url(url)
                if not duplicate:
                    n = self.get_recipe(data, url)
                    self.logger.info("Found %d recipe(s)" % n)
                if self.link_depth > 0:
                    n = self.get_links(data)
                    self.logger.info("Added %d link(s) to queue" % n)
            except Exception as exc:
                self.logger.error("Processing %s failed" % url, exc_info = True)
            time.sleep(self.pause)

        if self.link_depth > 0:
            self.links = self.link_queue
            self.link_queue = [ ]
            self.link_depth -= 1
            self.process_links()

    def get_url(self, url):
        """
        Retrieve a page and parse it.  Takes a url and returns the parsed html."""

        tries = 0
        while tries <= self.max_retries:
            tries += 1
            self.logger.info("Retrieving %s (try %d)" % (url, tries))
            try:
                resp = requests.get(url, timeout = self.timeout)
                resp.raise_for_status()
            except HTTPError as exc:
                if resp.status_code == 404:
                    self.logger.error("Page not found: %s" % url)
                    break
                self.logger.warn("Request failed with status %d: %s" % (resp.status_code, url))
                time.sleep(self.retry_interval * tries)
                continue
            except Timeout as exc:
                self.logger.error("Timed out: %s" % url)
                time.sleep(self.retry_interval * tries)
                continue
            except Exception as exc:
                self.logger.error("Unexpected error: %s" % url, exc_info = True)
            break

        if tries > self.max_retries:
            raise Exception("Request failed, max retries exceeded: %s" %url)

        try:
            data = html.fromstring(resp.content)
        except Exception as exc:
            raise

        return data

    def get_links(self, data):
        """
        Extract links to other recipes from a page.  Links are added to the link queue 
        and the number of links found is returned.
        """

        count = 0
        for link in data.xpath("//*[@href]"):
            cleaned = re.sub("\?.*", "", link.attrib["href"])
            cleaned = urljoin(self.base_url, cleaned)
            if re.match(self.link_prefix, cleaned, flags = re.I) and \
              cleaned not in self.link_queue + self.links:
                self.link_queue.append(cleaned)
                self.logger.debug("Adding link %s" % cleaned)
                count += 1
        return count

    def update_recipes(self, update_existing = True):
        """Add fields to existing records and/or update existing fields."""

        for url in self.links:

            existing = self.collection.find_one({ "url": url })
            if existing is None:
                self.logger.info("Record does not exist: %s" % url)
                continue

            try:
                data = self.get_url(url)
                records = self.extract(data, url)
            except:
                self.logger.error("Processing failed for %s" % url, exc_info = True)
                continue

            for record in records:
                try:
                    if update_existing:
                        updates = record
                    else:
                        updates = dict([ (k, v) for k, v in record.iteritems() if k not in existing ])
                    updates["update_time"] = datetime.utcnow()
                    self.collection.update_one({ "url": url }, { "$set": updates })
                except Exception as exc:
                    self.logger.error("Could not update record: %s" % record["url"], exc_info = True)
                    continue
                self.logger.info("Updated %s" % url)

            time.sleep(self.pause)

    def get_recipe(self, data, url):
        """Extract a recipe from a page and store it according the method specified in the profile."""

        records = self.extract(data, url)
        if len(records) > 0:
            try:
                self.collection.insert_many(records)
            except Exception as exc:
                self.logger.error("Could not insert records!", exc_info = True)
        return len(records)

    def extract_from_json_ld(self, data, url):
        """Extract recipes from json-ld.  Fields are copied directly from json into a mongo document."""

        scripts = data.xpath("//script[@type='application/ld+json']")
        records = [ ]

        for scr in scripts:

            try:
                data = json.loads(scr.text)
            except:
                continue

            if not isinstance(data, dict):
                continue

            record = dict([ (k, v) for k, v in data.iteritems() if k in self.store_fields ])
            if "recipeIngredient" not in record and "ingredients" in data:
                record["recipeIngredient"] = data["ingredients"]

            record["url"] = url
            record["collect_time"] = datetime.utcnow()

            if self.validate(record):
                records.append(record)

        return records

    def extract_from_html(self, data, url):
        """Extract recipes from html tags.  Fields are extracted based on rules defined in the method."""

        records = [ ]
        self.logger.debug("Found %d recipes in %s" % (len(data.xpath(self.scope)), url))
        for rcp in data.xpath(self.scope):

            record = { }
            for prop in [ "name", "recipeYield", "author" ]:
                record[prop] = self.extract_text(prop, rcp)
            for prop in [ "image" ]:
                record[prop] = self.extract_attribute(prop, [ "content", "src" ], data)
            for prop in [ "totalTime", "prepTime", "cookTime", "datePublished" ]:
                record[prop] = self.extract_attribute(prop, [ "content" ], rcp)
            # I have no idea if cookingMethod should be text or a list because I've never seen it so
            # using the most general option for it
            for prop in [ "recipeIngredient", "recipeInstructions", "cookingMethod",
                          "recipeCategory", "recipeCuisine" ]:
                record[prop] = self.extract_list(prop, rcp)

            # Older versions of the schema use "ingredients" rather than "recipeIngredient"
            if not record["recipeIngredient"]:
                record["recipeIngredient"] = self.extract_list("ingredients", rcp)

            record = dict([ (k, v) for k, v in record.iteritems() if k in self.store_fields ])
            record["url"] = url
            record["collect_time"] = datetime.utcnow()

            if self.validate(record):
                records.append(record)

        return records

    def validate(self, record):
        """Check for missing fields."""

        self.logger.debug("Validating %s" % record["url"])

        # Remove empty fields
        for field in record.keys():
            if record[field] in [ None, "", [ ], { } ]:
                del record[field]

        # Check for missing fields
        missing = [ field for field in self.required_fields if field not in record.keys() ]
        if len(missing) > 0:
            self.logger.warn("recipe in %s: missing %s" % (record["url"], ", ".join(missing)))
            return False

        return True

    def extract_attribute(self, property, attributes, data):
        """Extract timing information: might be a tag attribute rather than tag text."""

        values = self.get_property(property, data)
        if values:
            for attr in attributes:
                try:
                    return values[0].attrib[attr]
                except:
                    continue
            return self.concat_text(values[0])

    def extract_text(self, property, data):
        """Extract a single-valued field by concatenating text in subelements."""

        values = self.get_property(property, data)
        if len(values) != 1:
            self.logger.debug("Expected one match for %s but found %d!" % (property, len(values)))
        if values:
            return self.concat_text(values[0])

    def extract_list(self, property, data):
        """
        Extract a list of values by concatenating text in subelements of all matching 
        elements, unless there is only one element returned; in that case use that
        element's children.

        Sometimes each item in a list will be tagged with schema fields, but sometimes 
        only the container will be, in which case, we want it's child elements.
        """

        values = self.get_property(property, data)
        if len(values) == 1:
            return [ self.concat_text(child) for child in values[0].getchildren() ]
        else:
            return [ self.concat_text(val) for val in values ]

    def get_property(self, property, data):
        """
        Get the property from the schema scope if possible, otherwise anywhere.
        Could backfire if there are multiple recipe scopes, or inherited properties that
        could occur in other objects but in my experience, this has never happened.
        """

        values = data.xpath("%s//*[@%s='%s']" % (self.scope, self.attribute, property))
        if len(values) == 0:
            values = data.xpath("//*[@%s='%s']" % (self.attribute, property))
        return values

    def concat_text(self, elem):
        """Concatenate text from all children, stripping extra whitespace."""

        s = u" ".join([ frag.strip() for frag in elem.itertext() if re.search("\S", frag) ]) 
        return re.sub(" (\W )", "\\1", s)


