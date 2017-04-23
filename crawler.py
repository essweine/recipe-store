#!/usr/bin/env python

import argparse, logging, importlib, json
import sys, traceback
from pymongo import MongoClient

from collection.collector import Collector
from collection.profile_builder import ProfileBuilder

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

def main(args):

    logger = init_logging(args)
    logger.debug("Logging initialized")

    if args.subcommand == "build":
        try:
            profile = ProfileBuilder(args.url)
        except Exception as exc:
            raise
        sys.__stdout__.write("\n%s\n" % str(profile))
        return

    try:
        config = json.loads(open(args.config).read())
    except Exception as exc:
        raise
    logger.debug("Configuration initialized")

    try:
        profile = importlib.import_module("profiles." + args.profile)
    except Exception as exc:
        raise
    logger.debug("Profile initialized")

    try:
        client = MongoClient(host = config["mongo"]["host"], port = config["mongo"]["port"])
        db = client[config["mongo"]["db"]]
        if args.collection is None:
            collection = db[args.profile]
        else:
            collection = db[args.collection]
    except Exception as exc:
        raise
    logger.debug("Mongo initialized")

    # Make collection and wait time available to profile
    profile.collection = collection
    profile.wait = args.wait

    if args.link_file is None:
        links = profile.generate_links(*args.profile_args)
    else:
        links = [ url.strip() for url in open(args.link_file) ]

    coll = Collector(collection, links, profile.site_profile, 
                    store_fields = config["collector"]["store_fields"],
                    required_fields = config["collector"]["required_fields"],
                    link_depth = args.depth, pause = args.wait)
    coll.process_links()

    client.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "recipe collection utility")
    subparsers = parser.add_subparsers(help = "subcommands", dest = "subcommand")
    
    build = subparsers.add_parser("build", help = "attempt to build a profile for site")
    build.add_argument("url", metavar = "URL", help = "attempt to build a profile based on %(metavar)s")

    collect = subparsers.add_parser("collect", help = "collect recipes based on a profile")
    collect.add_argument("-p", "--profile", metavar = "SOURCE", dest = "profile", required = True,
                        help = "use profile for %(metavar)s")
    collect.add_argument("-a", "--profile-args", metavar = "ARGS", dest = "profile_args", nargs = "*",
                        help = "pass %(metavar)s to link generation function")
    collect.add_argument("-o", "--link-file", metavar = "FILE", dest = "link_file", default = None,
                        help = "use list of urls in %(metavar)s instead of link generation function")
    collect.add_argument("-m", "--mongo-collection", metavar = "COLLECTION", dest = "collection", default = None,
                        help = "store recipes in mongo collection %(metavar)s [default: <profile name>]")
    collect.add_argument("-c", "--config", metavar = "FILE", dest = "config", default = "config.json",
                        help = "use storage options in %(metavar)s [default: %(default)s]")
    collect.add_argument("-w", "--wait", metavar = "SECONDS", dest = "wait", default = 10, type = int,
                        help = "wait %(metavar)s between requests [default: %(default)d]")
    collect.add_argument("-d", "--depth", metavar = "N", dest = "depth", default = 0, type = int,
                        help = "follow links to depth %(metavar)s [default: %(default)d]")

    parser.add_argument("-l", "--log-level", metavar = "LOGLEVEL", dest = "log_level", default = "INFO",
                        help = "set the log level to %(metavar)s [default: %(default)s]")
    parser.add_argument("-f", "--log-file", metavar = "LOGFILE", dest = "log_file", default = None,
                        help = "write logs to %(metavar)s, [default: stdout]")

    args = parser.parse_args()

    try:
        main(args)
    except:
        sys.__stderr__.write(traceback.format_exc())
        sys.exit(1)

