#!/usr/bin/env python

import argparse
import sys, traceback, logging
import re, json
from math import ceil
from cmd import Cmd
import readline

from pymongo import MongoClient

from collection import manager

class Pager(Cmd, object):

    def __init__(self, lines, line_length, last_page):
        
        Cmd.__init__(self)
        self.lines = lines
        self.line_length = line_length
        self.last_page = last_page
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

class FieldList(Pager):

    def __init__(self, lines, line_length, values, field):

        last_page = int(ceil(values["total"] / float(lines)))
        Pager.__init__(self, lines, line_length, last_page)
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

class RecipeList(Pager):

    def __init__(self, lines, line_length, recipes, mgr):

        last_page = int(ceil(recipes["total"] / float(lines)))
        Cmd.__init__(self)
        Pager.__init__(self, lines, line_length, last_page)
        self.recipes = recipes
        self.mgr = mgr
        self.prompt = "recipes (page %d of %d): " % (1, self.last_page)
        self.display_page(0)

    def do_recipe(self, num):
        """
        Display recipe <n>.
        """

        try:
            recipe = int(num.strip()) - 1
        except Exception as exc:
            sys.__stderr__.write("Invalid recipe number!\n")
            return

        if recipe < 0 or recipe >= len(self.recipes["objects"]):
            sys.__stderr__.write("Invalid recipe number!\n")
            return

        try:
            name = self.recipes["objects"][recipe]["name"]
            rcp = self.mgr.search(name = name, projection = manager.RECIPE_PROJECTION)
            if len(rcp) == 0:
                raise Exception("No recipes found!")
        except Exception as exc:
            sys.__stderr__.write("Recipe could not be retrieved!\n")
            return

        rcp = rcp["objects"][0]
        sys.__stdout__.write("\n%s\n\n" % rcp["name"])
        for field, text in zip([ "recipeYield", "totalTime", "prepTime", "cookTime" ],
                               [ "Yield", "Total time", "Prep time", "Cooking time" ]):
            if field in rcp:
                sys.__stdout__.write("%s: %s\n" % (text, rcp[field]))
        sys.__stdout__.write("\n")

        for ingredient in rcp["recipeIngredient"]:
            sys.__stdout__.write("%s\n" % ingredient)
        sys.__stdout__.write("\n")
        for instruction in rcp["recipeInstructions"]:
            sys.__stdout__.write("%s\n\n" % self.line_breaks(instruction))

    def line_breaks(self, text):

        lines = [ ]
        current = [ ]
        length = 0
        for word in text.split():
            if length + len(word) + 1 < self.line_length:
                current.append(word)
                length += len(word) + 1
            else:
                lines.append(current)
                current = [ ]
                length = 0
        lines.append(current)
        return "\n".join([ " ".join(line) for line in lines ])

    def display_page(self, page):

        try:
            super(RecipeList, self).display_page(page)
        except Exception as exc:
            sys.__stderr__.write("%s\n" % str(exc))
            return

        first, last = page * self.lines, min([ (page + 1) * self.lines, len(self.recipes["objects"]) ])
        current = first
        sys.__stdout__.write("\n")
        for rcp in self.recipes["objects"][first:last]:
            current += 1
            sys.__stdout__.write("  %4d. %s\n" % (current, rcp["name"]) )
        sys.__stdout__.write("\n")
        self.prompt = "recipes (page %d of %d): " % (page + 1, self.last_page)

class RecipeSearch(Cmd):

    def __init__(self, mgr, nrows, ncols):

        Cmd.__init__(self)
        self.mgr = mgr
        self.nrows = nrows
        self.lines = nrows - 4
        self.ncols = ncols
        self.line_length = ncols - 4
        self.prompt = "main menu: "
        self.search_params = {
            "recipeCategory": [ ],
            "recipeCuisine": [ ],
            "operator": "all",
        }

    def do_field(self, field):
        """
        Get a list of all possible field values.  Only do this for enumerated fields
        such as recipeCategory or recipeCuisine!
        """

        try:
            values = self.mgr.get_enumerated_values(field, include_count = True)
        except Exception as exc:
            raise

        if values["total"] == 0:
            sys.__stdout__.write("No results!\n")
            return

        fl = FieldList(self.lines, self.line_length, values, field)
        fl.cmdloop()

    def do_params(self, param):
        """
        Display search constraints.
        """

        if param and param not in self.params:
            sys.__stderr__.write("Invalid parameter\n")
            return
        elif param:
            sys.__stdout__.write("%s = %s\n" % (param, self.search_params[param]))
        else:
            for param in self.search_params:
                sys.__stdout__.write("%s = %s\n" % (param, self.search_params[param]))

    def do_set(self, args):
        """
        Set search constraints.
        Syntax is param_name = param_value(s); use a comma-separated list for multiple
        Valid parameters are recipeCategory, recipeCuisine, operator
        Valid operators are all (= boolean and), any (= boolean or)
        """
        m = re.match("(\w+)\s*=\s*(.*)", args.strip())
        if not m:
            sys.__stderr__.write("Unable to parse arguments\n")
            return

        param, values = m.groups()
        if "," in values:
            values = [ val.strip() for val in values.split(",") ]
        elif param in [ "recipeCategory", "recipeCuisine" ]:
            values = [ values ]

        if param not in [ "recipeCategory", "recipeCuisine", "operator" ]:
            sys.__stderr__.write("Invalid parameter\n")
            return

        if param == "operator" and values not in [ "any", "all" ]:
            sys.__stderr__.write("Invalid operator\n")
            return

        self.search_params[param] = values

    def do_reset(self, param):
        """
        Reset search constraints.
        """

        if param and param not in self.params:
            sys.__stderr__.write("Invalid parameter\n")
            return
        elif param in [ "recipeCategory", "recipeCuisine" ]:
            self.search_params[param] = [ ]
        elif param == "operator":
            self.search_params[param] = "all"
        else:
            self.search_params = {
                "recipeCategory": [ ],
                "recipeCuisine": [ ],
                "operator": "all",
            }

    def do_search(self, text):
        """
        Search recipes, with the currently set constraints applied.
        """

        recipes = self.mgr.search(
                text = text, 
                recipeCategory = self.search_params["recipeCategory"], 
                recipeCuisine = self.search_params["recipeCuisine"],
                op = "$and" if self.search_params["operator"] == "all" else "$or"
        )
        if recipes["total"] == 0:
            sys.__stdout__.write("No results!\n")
            return

        rl = RecipeList(self.lines, self.line_length, recipes, self.mgr)
        rl.cmdloop()

    def do_count(self, args):
        """
        Display total number of recipe in this collection.
        """

        sys.__stdout__.write("%d\n" % self.mgr.count())

    def do_width(self, w):
        """
        Set the screen width to <n>.
        """

        try:
            ncols = int(w.strip())
        except Exception as exc:
            sys.__stderr__.write("Invalid width\n")
            return

        self.line_length = ncols

    def do_quit(self, args):
        """
        Quit this program.
        """

        return True

def init_logging(args):

    logger = logging.getLogger()
    logger.setLevel(args.log_level.upper())
    if args.log_file is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(args.log_file)
    formatter = logging.Formatter("[%(levelname)s:%(module)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_terminal_size():
    import fcntl, termios, struct
    empty = struct.pack("HHHH", 0, 0, 0, 0)
    filled = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, empty)
    nrows, ncols, hwidth, vwidth = struct.unpack("HHHH", filled)
    return nrows, ncols

def main(args):

    logger = init_logging(args)

    try:
        config = json.loads(open(args.config).read())
    except Exception as exc:
        raise
    logger.debug("Configuration initialized")

    try:
        mgr = manager.Manager(config["mongo"], args.collection)
    except Exception as exc:
        raise

    # Attempt to get screen size, requires unix-specific services
    try:
        nrows, ncols = get_terminal_size()
    except Exception as exc:
        nrows, ncols = 20, 80
        sys.__stderr__.write(traceback.format_exc())

    if args.screen is not None:
        m = re.match("(\d+)x(\d+)", args.screen.strip())
        if m:
            nrows, ncols = int(m.group(1)), int(m.group(2))
        else:
            logger.warn("Unable to parse screen dimensions!")

    top = RecipeSearch(mgr, nrows, ncols)
    top.cmdloop("Command line recipe search utility.\nType help for more info.\n")

if __name__ == "__main__":

    parser = argparse.ArgumentParser("recipe search utility")
    parser.add_argument("-c", "--config", metavar = "FILE", dest = "config", default = "config.json",
                        help = "use storage options in %(metavar)s [default: %(default)s]")
    parser.add_argument("-m", "--mongo-collection", metavar = "COLLECTION", dest = "collection", required = True,
                        help = "store recipes in mongo collection %(metavar)s")
    parser.add_argument("-s", "--screen", metavar = "NxN", dest = "screen", default = None,
                        help = "assume %(metavar)s display [default: autodetect]")
    parser.add_argument("-l", "--log-level", metavar = "LOGLEVEL", dest = "log_level", default = "WARN",
                        help = "set the log level to %(metavar)s [default: %(default)s]")
    parser.add_argument("-f", "--log-file", metavar = "LOGFILE", dest = "log_file", default = None,
                        help = "write logs to %(metavar)s, [default: stdout]")

    args = parser.parse_args()

    try:
        main(args)
    except SystemExit:
        sys.exit(0)
    except Exception as exc:
        sys.__stderr__.write(traceback.format_exc())
        sys.exit(1)

