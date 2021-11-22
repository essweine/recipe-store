import time
import requests
from lxml import html

# Settings for Gourmet

site_profile = {
    "display_name": "Gourmet",
    "base_url": "http://www.epicurious.com",
    "link_prefix": "/recipes/food/views",
    "extract_method": "json-ld",
}

def generate_links(first_page, last_page):

    links = set([ ])
    for p in range(int(first_page), int(last_page) + 1):
        resp = requests.get(f"{site_profile['base_url']}/source/gourmet?page={p}")
        content = html.fromstring(resp.content)
        for link in content.xpath(f".//a[starts-with(@href, '{site_profile['link_prefix']}')]"):
            links.add(f"{site_profile['base_url']}{link.attrib['href']}")
        time.sleep(2)
    return list(links)

