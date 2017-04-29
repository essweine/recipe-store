# Settings for Saveur

import logging
import requests, time
from urllib import quote

logger = logging.getLogger(__name__)

site_profile = {
    "base_url": "http://www.saveur.com",
    "link_prefix": "http://www.saveur.com",
    "extract_method": "RDFa",
}

# Finished page 89, 91, 93, 133+
def generate_links(first_page, last_page = None):

    if last_page is None:
        last_page = first_page

    api_url = "http://www.saveur.com/sites/all/modules/bonnier/search_hubs/includes/search_hubs_solr.inc.php"
    api_params = [ ['filters[filter0][filterType]', 'categories'], ['filters[filter0][filterNum]', '0'],
                   ['filters[filter0][operator]', 'and'], ['filters[filter0][tids]', ''],
                   ['filters[filter1][filterType]', 'categories'], ['filters[filter1][filterNum]', '1'],
                   ['filters[filter1][operator]', 'and'], ['filters[filter1][tids]', ''],
                   ['filters[filter2][filterType]', 'categories'], ['filters[filter2][filterNum]', '2'],
                   ['filters[filter2][operator]', 'and'], ['filters[filter2][tids]', ''],
                   ['filters[filter3][filterType]', 'categories'], ['filters[filter3][filterNum]', '3'],
                   ['filters[filter3][operator]', 'and'], ['filters[filter3][tids]', ''],
                   ['filters[filter4][filterType]', 'categories'], ['filters[filter4][filterNum]', '4'],
                   ['filters[filter4][operator]', 'and'], ['filters[filter4][tids]', ''],
                   ['filters[filter5][filterType]', 'categories'], ['filters[filter5][filterNum]', '5'],
                   ['filters[filter5][operator]', 'and'], ['filters[filter5][tids]', ''],
                   ['scope[primaryChannels][]', 'recipes'], ['scope[tags]', ''],
                   ['scope[excludeTags]', ''], ['scope[andOr]', 'AND'], ['scope[bundle][]', 'basic_content'],
                   ['scope[itemsPerPage]', '48'], ['scope[sortBy]', 'date'], ['scope[sortOrder]', 'desc'],
                   ['string', ''], ['page', '0'] ]

    def prmstr(prm): return "&".join([ "%s=%s" % (quote(p[0]), quote(p[1])) for p in prm ])

    sess = requests.Session()
    links = [ ]

    def get_page(page):
        api_params[-1][1] = str(page)
        tries = 0
        while tries < 3:
            try:
                sess.get("http://www.saveur.com/recipes-search?page=%d" % page)
                r = sess.get("%s?%s" % (api_url, prmstr(api_params)) )
                js = r.json()
            except Exception as exc:
                logger.error("Request failed", exc_info = True)
                time.sleep(tries * 1)
                tries += 1
                continue
            break

        if tries == 3:
            raise Exception("Could not retrieve page %d" % page)

        for item in js["items"]:
            links.append("%s/%s" % (site_profile["base_url"], item["path"]))

    for page in range(int(first_page), int(last_page) + 1):
        try:
            get_page(page)
            logger.info("Got page %d" % page)
            time.sleep(wait)
        except Exception as exc:
            logger.error("Retrieval failed for page %d" % page)
            continue

    return links

