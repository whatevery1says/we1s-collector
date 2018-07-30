#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A script for counting zip file contents

Count all files inside zipfiles in the current tree:
    ./zipcount.py

Count all files inside zipfiles in the tree of a subdirectory:
    ./zipcount.py myfolder

Count all filenames matching the namefilter 'json':
    ./zipcount.py -f json

Count all filenames matching the namefilter 'txt' in a subdirectory tree:

    ./zipcount.py myfolder -f txt
"""


import argparse
import os
import zipfile


def main(filespath, namefilter=''):
    """Loop through zip files, count files (with optional namefilter)"""

    os.chdir(filespath)
    count = 0
    for (dirname, _dirs, files) in os.walk(filespath):
        for filename in files:
            if filename.endswith('.zip'):  # scan for zip files
                filepath = os.path.join(dirname, filename)
                print('\n', filepath, '\n')
                source = zipfile.ZipFile(filepath, 'r')  # read zip

                # test for bad filename char
                for afile in source.filelist:
                    if namefilter:
                        if namefilter in afile.filename:
                            count += 1
                            print('   ', afile.filename)
                    else:
                        count += 1
                        print('   ', afile.filename)
    print('Files counted:\n', count)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description=__doc__)
    PARSER.add_argument('dir', nargs='?', default='',
                        help='directory tree to process')
    PARSER.add_argument('-n', '--namefilter', default='',
                        help='pattern for content filenames, e.g. json')
    ARGS = PARSER.parse_args()
    main(os.path.abspath(ARGS.dir), ARGS.namefilter)
