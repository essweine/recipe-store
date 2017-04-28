from cmd import Cmd
from math import ceil

class Pager(Cmd, object):

    def __init__(self, lines, line_length, total_items):
        
        Cmd.__init__(self)
        self.lines = lines
        self.line_length = line_length
        self.last_page = int(ceil(total_items) / float(lines))
        self.current = 0

    def do_page(self, num):
        """
        Go to page <n> or redisplay current page.
        """

        if num == "":
            page = self.current
        else:
            try:
                page = int(num.strip()) - 1
            except Exception as exc:
                sys.__stderr__.write("Invalid page number!\n")
                return
        
        self.display_page(page)

    def do_next(self, args):
        """
        Go to next page
        """
        self.display_page(self.current + 1)

    def do_previous(self, args):
        """
        Go to previous page
        """
        self.display_page(self.current - 1)

    def do_back(self, args):
        """
        Exit field view.
        """
        return True

    def do_quit(self, args):
        """
        Quit this program.
        """
        raise SystemExit

    def display_page(self, page):

        if page < 0:
            raise Exception("Cannot go beyond first page")
        elif page >= self.last_page:
            raise Exception("Cannot go beyond last page")


