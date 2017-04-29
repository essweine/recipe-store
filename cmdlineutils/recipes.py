from base import RecipeUtilPager

from collection.manager import RECIPE_PROJECTION, RECIPE_INFO_PROJECTION

class RecipeList(RecipeUtilPager, object):

    def __init__(self, lines, line_length, recipes, mgr):

        super(RecipeList, self).__init__(lines, line_length, recipes["total"])
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
            self.stderr.write("Invalid recipe number!\n")
            return

        if recipe < 0 or recipe >= len(self.recipes["objects"]):
            self.stderr.write("Invalid recipe number!\n")
            return

        try:
            name = self.recipes["objects"][recipe]["name"]
            rcp = self.mgr.search(name = name, projection = RECIPE_PROJECTION)
            if len(rcp) == 0:
                raise Exception("No recipes found!")
        except Exception as exc:
            self.stderr.write("Recipe could not be retrieved!\n")
            return

        rcp = rcp["objects"][0]
        self.stdout.write("\n%s\n\n" % rcp["name"])
        for field, text in zip([ "recipeYield", "totalTime", "prepTime", "cookTime" ],
                               [ "Yield", "Total time", "Prep time", "Cooking time" ]):
            if field in rcp:
                self.stdout.write("%s: %s\n" % (text, rcp[field]))
        self.stdout.write("\n")

        for ingredient in rcp["recipeIngredient"]:
            self.stdout.write("%s\n" % ingredient)
        self.stdout.write("\n")
        for instruction in rcp["recipeInstructions"]:
            self.stdout.write("%s\n\n" % self.line_breaks(instruction))

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
            self.stderr.write("%s\n" % str(exc))
            return

        first, last = page * self.lines, min([ (page + 1) * self.lines, len(self.recipes["objects"]) ])
        current = first
        self.stdout.write("\n")
        for rcp in self.recipes["objects"][first:last]:
            current += 1
            self.stdout.write("  %4d. %s\n" % (current, rcp["name"]) )
        self.stdout.write("\n")
        self.prompt = "recipes (page %d of %d): " % (page + 1, self.last_page)

