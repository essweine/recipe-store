import sys, traceback
from cmd import Cmd
from pager import Pager

from collection.manager import RECIPE_PROJECTION, RECIPE_INFO_PROJECTION

class RecipeList(Pager):

    def __init__(self, lines, line_length, recipes, mgr):

        Cmd.__init__(self)
        Pager.__init__(self, lines, line_length, recipes["total"])
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
            rcp = self.mgr.search(name = name, projection = RECIPE_PROJECTION)
            if len(rcp) == 0:
                raise Exception("No recipes found!")
        except Exception as exc:
            sys.__stderr__.write("Recipe could not be retrieved!\n")
            sys.__stderr__.write(traceback.format_exc())
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

