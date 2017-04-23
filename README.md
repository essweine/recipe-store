# Recipe collection utility

Retrieve recipes from cooking sites and store them in a mongo database.

## General collection options

This program uses http://schema.org/Recipe to parse the recipes and selectively
store the field values.

It also contains a utility for building a profile based on a url containing a
recipe.  Unfortunately, you are on your own for a link generation function.

You can, however, override use of a link generation function by providing a
file containing a list of urls to check (one url per line).

Eventually I will write utilities for doing something with the recipes.

## Profiles

A profile module must contain a site_profile dictionary of parameters and a link
generation function; arguments to this function can be specified on the crawler
command line and passed to the function.  The crawler script makes the mongo
collection available to the profile when it is loaded.

### Included profiles

#### Bon Appetit

Arguments are first issue date and last issue date to collect recipes from
(inclusive).  The date format is yyyy-mm-dd.

#### Gourmet

Epicurious has an archive of recipes from Gourmet, organized by page.  Arguments
to the link generator are first and last page (inclusive).  There are 1136 pages,
with 10 recipes per page.

#### New York Times

NYT does not seem to have a centralized page, except for the main cooking page.
cooking.nytimes.com is always added to the returned list of links, and this can
be augmented by specifying the size of a random sample of previously collected
articles.  You must change the link depth to at least 1 to get any new results.

#### Saveur

Saveur organizes their recipes by page.  Arguments are first and last page to 
retrieve (inclusive).  At the time of this writing, there are 153 pages.
