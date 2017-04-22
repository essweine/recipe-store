import requests, time
from urlparse import urlparse, urljoin
from lxml import html

class ProfileBuilder(object):

    def __init__(self, url):
        """Guesses parameters for a site based on a sample url."""

        self.url = url

        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = html.fromstring(resp.content)
        except Exception as exc:
            raise

        result = urlparse(url)
        self.base_url = "%s://%s" % (result.scheme, result.netloc)

        if data.xpath("//script[@type='application/ld+json']"):
            self.extract_method = "json-ld"
        elif data.xpath("//*[@itemtype='http://schema.org/Recipe']"):
            self.extract_method = "microdata"
        elif data.xpath("//*[@typeof='Recipe']"):
            self.extract_method = "RDFa"
        else:
            self.extract_method = None

        prefixes = set()
        for link in data.xpath("//*[@href]"):
            r = urlparse(link.attrib["href"])
            if r.netloc and r.netloc != result.netloc:
                continue
            prefix = "/".join([ e1 for e1, e2 in zip(result.path[:-1].split("/"), r.path.split("/")) if e1 == e2 ])
            prefixes.add(prefix)

        if len(prefixes) > 0:
            self.link_prefix = urljoin(self.base_url, sorted(prefixes, key = lambda p: len(p))[-1])
        else:
            self.link_prefix = self.base_url

    def get_profile(self):

        return {
            "base_url": self.base_url,
            "link_prefix": self.link_prefix,
            "extract_method": self.extract_method,
        }

    def __str__(self):

        s = "Settings detected in %s\n" % self.url
        for setting in [ "base_url", "link_prefix", "extract_method" ]:
            s += "%-16s: %s\n" % (setting, self.__dict__[setting])
        return s

