"""WSK command line interface for WE1S (WhatEvery1Says)
"""

import argparse

from search import get_authenticated_session, search_querylist


def main(args):
    """Collection of actions to execute on run."""
    session = get_authenticated_session()

    if args.queries:
        search_querylist(session, fname='queries.csv', bagify=args.bagify,
                         outpath=args.outpath, zip_output=args.bagify)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description=__doc__)
    PARSER.add_argument('-b', '--bagify', action='store_true', help='')
    PARSER.add_argument('-o', '--outpath', help='output path, e.g. "../output"')
    PARSER.add_argument('-q', '--queries', help='specify query file path, e.g. queries.csv')
    PARSER.add_argument('-z', '--zip', action='store_false', help='zip the json output')
    ARGS = PARSER.parse_args()
    main(ARGS)
