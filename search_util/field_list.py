import sys
from pager import Pager

class FieldList(Pager):

    def __init__(self, lines, line_length, values, field):

        Pager.__init__(self, lines, line_length, values["total"])
        self.values = values
        self.field = field
        self.prompt = "viewing %s (page %d of %d): " % (field, 1, self.last_page)
        self.display_page(0)

    def display_page(self, page):

        try:
            super(FieldList, self).display_page(page)
        except Exception as exc:
            sys.__stderr__.write("%s\n" % str(exc))
            return

        sys.__stdout__.write("\n")
        self.current = page
        first, last = page * self.lines, min([ (page + 1) * self.lines, len(self.values["objects"]) ])
        for val in self.values["objects"][first:last]:
            sys.__stdout__.write("%-30s\t%d\n" % (val["value"], val["count"]) )
        sys.__stdout__.write("\n")
        self.prompt = "viewing %s (page %d of %d): " % (self.field, page + 1, self.last_page)

