import re
import traceback

from .base import RecipeUtilBase

class RecipeAdmin(RecipeUtilBase, object):

    def __init__(self, mgr):

        super(RecipeAdmin, self).__init__()
        self.mgr = mgr
        self.prompt = "admin: "

    def do_index(self, args):
        """
        Create an index.

        index text default OR
        index text name=<name> lang=<lang> fields=<name:weight>,<name:weight>,...
        index name=<name> fields=<name:order>, <name:order>

        name is optional
        lang should be a valid pymongo language option, default is "en"
        order is asc[ending] or desc[ending]
        """

        arg_types = {
            "name": "string",
            "fields": "pairs",
            "text": "store_true",
            "default": "store_true",
            "lang": "string",
        }
        try:
            options = self.parse_args(args, arg_types)
        except Exception as exc:
            self.stderr.write("Could not parse options!\n")
            self.stderr.write(traceback.format_exc())
            return

        try:
            if options.get("text", False) and options.get("default", False):
                self.mgr.create_default_text_index()
            elif options.get("text", False):
                options["fields"] = [ (f, 1) if len(f) == 1 else f for f in options["fields"] ]
                fields, weights = zip(*options["fields"])
                name = options.get("name", "recipe_text")
                lang = options.get("lang", "en")
                self.mgr.create_text_index(fields, name = name, default_language = lang,
                    weights = dict(zip(fields, [ float(w) for w in weights ])) )
            else:
                name = options.get("name", None)
                self.mgr.create_index(options["fields"], name)
        except Exception as exc:
            self.stderr.write("Unable to create index\n")
            self.stderr.write(traceback.format_exc())
            return

    def do_info(self, args):
        """
        Display basic information about the collection.
        """

        try:
            self.stdout.write("Total recipes %d\n" % self.mgr.count())
            self.stdout.write("\nIndex Information\n")
            for name, index in self.mgr.list_indexes().items():
                self.stdout.write("%-18s %-12s %s\n" % (name, index["type"], index["fields"]))
            self.stdout.write("\n")
        except Exception as exc:
            self.stderr.write("Unable to retrieve index info!\n")
            self.stderr.write(traceback.format_exc())

    def do_drop(self, index):
        """
        Drop an index by name.
        """

        try:
            self.mgr.drop_index(index)
        except Exception as exc:
            seld.stderr.write("Operation failed!\n")
        self.stdout.write("Success!\n")

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

