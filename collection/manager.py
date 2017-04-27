import pymongo
import logging
import re

DEFAULT_PROJECTION = { "name": 1, "url": 1, "_id": 0 }

RECIPE_PROJECTION = { 
    "name": 1, 
    "recipeIngredient": 1,
    "recipeInstructions": 1,
    "recipeYield": 1,
    "totalTime": 1,
    "prepTime": 1,
    "cookTime": 1,
    "_id": 0
}

RECIPE_INFO_PROJECTION = {
    "url": 1,
    "datePublished": 1,
    "author": 1,
    "collect_time": 1,
    "update_time": 1,
    "_id": 0
}

DEFAULT_SORT = [ ("name", pymongo.ASCENDING) ]
TEXT_SCORE_SORT = [ ("score", { "$meta": "textScore" }) ]

class Manager(object):

    def __init__(self, mongo_config, collection):

        try:
            client = pymongo.MongoClient(host = mongo_config["host"], port = mongo_config["port"])
            db = client[mongo_config["db"]]
            self.collection = db[collection]
        except Exception as exc:
            raise
        self.logger = logging.getLogger(__name__)
 
    def count(self): return self.collection.count()

    def get_enumerated_values(self, field, include_count = False):
        """Get a list of values and optional counts."""

        prefixed = "$%s" % field
        unwind = { "$unwind": prefixed }
        query = {
            "$group": { 
                "_id": { "value": prefixed }
            }
        }
        if include_count:
            query["$group"]["count"] = { "$sum": 1 }
        sort = { "$sort": { "_id.value": pymongo.ASCENDING } }

        results = { "objects": [ ], "total": 0 }
        for result in [ res for res in self.collection.aggregate([ unwind, query, sort ]) ]:
            res = { "value": result["_id"]["value"] }
            if include_count:
                res["count"] = result["count"]
            results["objects"].append(res)
            results["total"] += 1
        return results

    def search(self, text = "", **kwargs):
        """
        Construct and perform a mongo query.
        
        Schema fields can be provided as keyword args (though not all are handled).  Text, 
        name, or url are intended to be mutually exclusive options, and further constrained by 
        category or cuisine (or other fields, when I get around to handling those).  If you
        need a somethine else, you can always use the find method directly on self.collection.

        The default projection is to return name and url.  A recipe projection (defined in this
        module) will return the recipe itself, but no other data.  The recipe info projection
        (also defined in this module) will return data about the recipe (url, author, date
        published, etc).  You can also provide your own projection; it will be passed to find
        as-is.

        The default sort is by name, asecending, unless a text search was done, in which case
        the text score, descending, is used.  You can provide your own sort criteria; it will
        also be passed to find as-is.
        """

        conditions = [ ]
        if text:
            conditions.append({ "$text": { "$search": text } })
        if "name" in kwargs:
            conditions.append({ "name": kwargs["name"] })
        if "url" in kwargs:
            conditions.append({ "url": kwargs["url"] })

        constraints = [ ]
        op = kwargs.get("op", "$and")
        for category in kwargs.get("recipeCategory", [ ]):
            constraints.append({ "recipeCategory": category })
        for cuisine in kwargs.get("recipeCuisine", [ ]):
            constraints.append({ "recipeCuisine": cuisine })
        constraints = self.make_clause(op, constraints)

        if len(conditions) == 0 and len(constraints) == 0:
            query = { }
        elif len(conditions) == 0:
            query = constraints
        elif len(constraints) == 0:
            query = self.make_clause("$and", conditions)
        else:
            query = { "$and": conditions + [ constraints ] }

        projection = kwargs.get("projection", DEFAULT_PROJECTION)
        if text:
            sort = kwargs.get("sort", TEXT_SCORE_SORT)
            projection["score"] = { "$meta": "textScore" }
        else:
            sort = kwargs.get("sort", DEFAULT_SORT)

        self.logger.debug("\nquery = %s\nprojection = %s\nsort = %s" % (query, projection, sort))

        results = { "objects": [ ], "total": 0 }
        for rcp in self.collection.find(query, projection, sort = sort):
            for field in [ "totalTime", "cookTime", "prepTime" ]:
                duration = rcp.get(field, None)
                if duration:
                    rcp[field] = self.convert_duration(duration)
            results["objects"].append(rcp)
            results["total"] += 1
        return results

    def make_clause(self, op, conditions):

        if len(conditions) == 0:
            return { }
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return { op: conditions }

    def create_default_text_index(self):
        """Set up an index on the name, ingredients, and instructions."""

        fields = [ "name", "recipeIngredient", "recipeInstructions" ]
        weights = { "name": 3, "recipeIngredient": 2, "recipeInstructions": 1 }
        self.create_text_index(fields, "recipe_text", "en", weights)

    def create_text_index(self, fields, name, default_language = "none", weights = { }):
        """Create a text index on the collection."""

        weights.update(dict([ (f, 1) for f in fields if f not in weights ]))

        # name, recipeIngredient, recipeInstructions
        return self.collection.create_index(
            [ (field, pymongo.TEXT) for field in fields ],
            name = name, 
            default_language = default_language,
            weights = weights
        )

    def list_indexes(self):
        """Return a list of indexes on the collection."""

        return self.collection.index_information()

    def convert_duration(self, duration):
        """Convert ISO duration to something more readable.  For display purposes."""

        spans = [ "years", "months", "days", "hours", "mins", "secs" ]
        m = re.search("P(\d+Y)?(\d+M)?(\d+D)?T(\d+H)?(\d+M)?(\d+S)?", duration, flags = re.I)
        return ", ".join([ "%s %s" % (dur[:-1], inc) for dur, inc in zip(m.groups(), spans) if dur is not None ])
