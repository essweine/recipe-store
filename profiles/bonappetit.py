# Settings for Bon Appetit

import requests, time
from calendar import monthrange
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

site_profile = {
    "display_name": "Bon Appetit",
    "base_url": "http://www.bonappetit.com",
    "link_prefix": "http://www.bonappetit.com/recipe/",
    "extract_method": "json-ld",
}

def generate_links(first_issue, last_issue = None):

    if last_issue is None:
        last_issue = first_issue

    links = [ ]
    api_url = "http://www.bonappetit.com/api/search"
    api_params = "page=%d&types=recipes&status=published&issueDate=%s&{}"

    def get_issue(pub_date):

        logger.info("Getting recipe list for %s" % pub_date)
        pg, next_pg = 1, True
        while next_pg:

            try:
                r = requests.get("%s?%s" % (api_url, api_params % (pg, pub_date)), timeout = 60)
                js = r.json()
            except Exception as exc:
                logger.error("Request failed for page %d" % pg, exc_info = True)
                break

            logger.info("Got page %d" % pg)
            if pg * int(js["query"]["size"]) < js["numFound"]:
                pg += 1
            else:
                next_pg = False

            for item in js["items"]:
                url = "%s%s" % (site_profile["base_url"], item["url"])
                links.append(url)

            time.sleep(wait)

    try:
        current = datetime.strptime(first_issue, "%Y-%m-%d")
        end = datetime.strptime(last_issue, "%Y-%m-%d")
    except:
        raise

    while current <= end:
        get_issue(current.strftime("%Y-%m-%d"))
        f, inc = monthrange(current.year, current.month)
        current += timedelta(days = inc)
    
    return links
