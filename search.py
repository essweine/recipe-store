#!/usr/bin/env python

import argparse
import sys, traceback, logging
import re, json
from math import ceil

from pymongo import MongoClient

from collection import manager
from cmdlineutils import RecipeUtil

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
        mgr = manager.Manager(config["mongo"], 
                              args.collection, 
                              config["collector"]["store_fields"])
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

    top = RecipeUtil(mgr, nrows, ncols)
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

