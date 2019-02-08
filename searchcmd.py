#!/usr/bin/env python3
"""WSK command line interface for WE1S (WhatEvery1Says)
usage examples:
    python searchcmd.py -o ../wskoutput -q queries.csv
    ./searchcmd.py -o ../wskoutput -q queries.csv
"""

import argparse
import sys

from search import get_authenticated_session, search_querylist


def main(args):
    """Collection of actions to execute on run."""
    session = get_authenticated_session()

    if args.queries:
        search_querylist(session, fname=args.queries, bagify=args.bagify,
                         outpath=args.outpath, zip_output=args.zip, scrub=args.scrub)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description=__doc__,
                                     usage='use "%(prog)s --help" for more information',
                                     formatter_class=argparse.RawTextHelpFormatter)
    PARSER.add_argument('-b', '--bagify', action='store_true', help='')
    PARSER.add_argument('-o', '--outpath', default='', help='output path, e.g. "../output"')
    PARSER.add_argument('-q', '--queries', help='specify query file path, e.g. queries.csv')
    PARSER.add_argument('-z', '--zip', action='store_false', help='zip the json output')
    PARSER.add_argument('-s', '--scrub', action='store_false', help='scrub article content, true by default')
    if not sys.argv[1:]:
        PARSER.print_help()
        PARSER.exit()
    ARGS = PARSER.parse_args()
    main(ARGS)
