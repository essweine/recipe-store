import sys, shlex, re
from cmd import Cmd
from math import ceil

class RecipeUtilBase(Cmd, object):

    def __init__(self):

        Cmd.__init__(self)
        self.stderr = sys.stderr

    def do_parse(self, args):

        params = self.parse_args(args)
        self.stdout.write("\n%s\n" % params)

    def parse_args(self, args, arg_types = { }):

        lex = shlex.shlex(args, posix = True)
        params = { }
        while True:
            try:
                token = lex.next()
                if token not in arg_types:
                    raise Exception("No arg type for %s" % token)

                if arg_types[token] == "store_true":
                    params[token] = True
                    continue
                elif lex.next() != "=":
                    raise Exception("Unable to parse value of %s" % token)

                if arg_types[token] == "string":
                    params[token] = lex.next()

                elif arg_types[token] == "list":
                    params[token] = [ lex.next() ]
                    while self.check(lex, ","):
                        params[token].append(lex.next())

                elif arg_types[token] == "pairs":
                    params[token] = [ self.get_pair(lex) ]
                    while self.check(lex, ","):
                        params[token].append(self.get_pair(lex))

            except StopIteration:
                break

            except Exception as exc:
                raise

        return params

    def check(self, lex, value):

        token = lex.next()
        if token != value:
            lex.push_token(token)
            return False
        else:
            return True

    def get_pair(self, lex):

        try:
            item, sep, value = lex.next(), lex.next(), lex.next()
            if sep != ":":
                raise Exception("Missing separator")
        except:
            raise
        return item, value

    def do_quit(self, args):
        """
        Quit this program.
        """
        return True

    def do_exit(self, args):
        """
        Quit this program.
        """
        return True

class RecipeUtilPager(RecipeUtilBase, object):

    def __init__(self, lines, line_length, total_items):
        
        super(RecipeUtilPager, self).__init__()
        self.lines = lines
        self.line_length = line_length
        self.last_page = int(ceil(total_items / float(lines)))
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
                self.stderr.write("Invalid page number!\n")
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

    def do_exit(self, args):
        """
        Quit this program.
        """
        raise SystemExit

    def display_page(self, page):

        if page < 0:
            raise Exception("Cannot go beyond first page")
        elif page >= self.last_page:
            raise Exception("Cannot go beyond last page")

