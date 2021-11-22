# Settings for NYT

site_profile = {
    "display_name": "New York Times",
    "base_url": "http://cooking.nytimes.com",
    "link_prefix": "http://cooking.nytimes.com/recipes",
    "extract_method": "json-ld",
}

def generate_links(count=0):

    links = [ "http://cooking.nytimes.com" ]
    for rcp in collection.aggregate([ { "$sample": { "size": int(count) } } ]):
        links.append(rcp["url"])
    return links

