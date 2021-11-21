from .base import RecipeUtilPager

class FieldList(RecipeUtilPager, object):

    def __init__(self, lines, line_length, values, field):

        super(FieldList, self).__init__(lines, line_length, values["total"])
        self.values = values
        self.field = field
        self.prompt = "viewing %s (page %d of %d): " % (field, 1, self.last_page)
        self.display_page(0)

    def display_page(self, page):

        try:
            super(FieldList, self).display_page(page)
        except Exception as exc:
            self.stderr.write("%s\n" % str(exc))
            return

        self.stdout.write("\n")
        self.current = page
        first, last = page * self.lines, min([ (page + 1) * self.lines, len(self.values["objects"]) ])
        for val in self.values["objects"][first:last]:
            self.stdout.write("%-30s\t%d\n" % (val["value"], val["count"]) )
        self.stdout.write("\n")
        self.prompt = "viewing %s (page %d of %d): " % (self.field, page + 1, self.last_page)

    def do_sort(self, options):
        """
        Re-sort list by name or count, ascending or descending.
        """

        try:
            field, order = options.split()
        except Exception as exc:
            self.stderr.write("Could not parse options!\n")
            return

        if field not in [ "value", "count" ]:
            self.stderr.write("Invalid option: %s!\n" % field)
            return

        if order not in [ "asc", "ascending", "desc", "descending" ]:
            self.stderr.write("Invalid option: %s!\n" % order)
            return

        self.values["objects"] = sorted(self.values["objects"], key = lambda obj: obj[field])
        if order in [ "desc", "descending" ]:
            self.values["objects"] = [ obj for obj in reversed(self.values["objects"]) ]

        self.display_page(0)

