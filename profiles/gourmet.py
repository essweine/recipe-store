# Settings for Gourmet

site_profile = {
    "base_url": "http://www.epicurious.com",
    "link_prefix": "http://www.epicurious.com/recipes/food/views/(?!0)",
    "extract_method": "microdata",
}

def generate_links(first_page, last_page):

    links = [ ]
    # Gourmet has 1136 recipes; they display 10 per page.
    pg_path = "/recipesmenus/gourmet/recipes?pageNumber=%d&pageSize=10&resultOffset=%d"
    for i in range(int(first_page), int(last_page) + 1):
        url = "%s%s" % (site_profile["base_url"], pg_path % (i, ((i - 1) * 10) + 1))
        links.append(url)
    return links

