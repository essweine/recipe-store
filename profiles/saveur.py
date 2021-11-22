# Settings for Saveur

import logging
import requests, time
from lxml import html

logger = logging.getLogger(__name__)

site_profile = {
    "display_name": "Saveur",
    "base_url": "http://www.saveur.com",
    "link_prefix": "http://www.saveur.com",
    "extract_method": "RDFa",
}

def generate_links(first_page, last_page=None):

    if last_page is None:
        last_page = int(first_page)

    links = set([])
    for p in range(int(first_page), int(last_page) + 1):
        resp = requests.get(f"{site_profile['base_url']}/tags/recipes/page/{p}")
        content = html.fromstring(resp.content)
        for link in content.xpath(".//a[@class='Post-link']"):
            links.add(link.attrib['href'])
        time.sleep(2)

    return links
