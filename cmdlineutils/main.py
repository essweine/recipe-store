#!/usr/bin/env python

import re, sys
from math import ceil

from collection import manager

from base import RecipeUtilBase
from fields import FieldList
from recipes import RecipeList
from admin import RecipeAdmin

class RecipeUtil(RecipeUtilBase, object):

    def __init__(self, mgr, nrows, ncols):

        super(RecipeUtil, self).__init__()
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
            self.stdout.write("No results!\n")
            return

        fl = FieldList(self.lines, self.line_length, values, field)
        fl.cmdloop()

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
            self.stdout.write("No results!\n")
            return

        rl = RecipeList(self.lines, self.line_length, recipes, self.mgr)
        rl.cmdloop()

    def do_admin(self, args):
        """
        Basic administration for the collection.
        """

        admin = RecipeAdmin(self.mgr)
        admin.cmdloop()

    def do_count(self, args):
        """
        Display total number of recipe in this collection.
        """

        self.stdout.write("%d\n" % self.mgr.count())

    def do_sample(self, size):

        if size == "":
            size = 1
        try:
            size = int(size.strip())
        except:
            self.stderr.write("Size must be a number")
            return

        recipes = self.mgr.sample(size)
        rl = RecipeList(self.lines, self.line_length, recipes, self.mgr)
        rl.cmdloop()

    def do_params(self, param):
        """
        Display search constraints.
        """

        if param and param not in self.search_params:
            self.stderr.write("Invalid parameter\n")
            return
        elif param:
            self.stdout.write("\n%s = %s\n\n" % (param, self.search_params[param]))
        else:
            self.stdout.write("\n")
            for param in self.search_params:
                self.stdout.write("%s = %s\n" % (param, self.search_params[param]))
            self.stdout.write("\n")

    def do_set(self, args):
        """
        Set search constraints.
        Syntax is param_name=param_value(s); use a comma-separated list for multiple
        Valid parameters are recipeCategory, recipeCuisine, operator
        Valid operators are all (= boolean and), any (= boolean or)
        """
        m = re.match("(\w+)\s*=\s*(.*)", args.strip())
        if not m:
            self.stderr.write("Unable to parse arguments\n")
            return

        param, values = m.groups()
        if "," in values:
            values = [ val.strip() for val in values.split(",") ]
        elif param in [ "recipeCategory", "recipeCuisine" ]:
            values = [ values ]

        if param not in [ "recipeCategory", "recipeCuisine", "operator" ]:
            self.stderr.write("Invalid parameter\n")
            return

        if param == "operator" and values not in [ "any", "all" ]:
            self.stderr.write("Invalid operator\n")
            return

        self.search_params[param] = values

    def do_reset(self, param):
        """
        Reset search constraints.
        """

        if param and param not in self.params:
            self.stderr.write("Invalid parameter\n")
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

    def do_width(self, w):
        """
        Set the screen width to <n>.
        """

        try:
            ncols = int(w.strip())
        except Exception as exc:
            self.stderr.write("Invalid width\n")
            return

        self.line_length = ncols


