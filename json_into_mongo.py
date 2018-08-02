#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""json_into_mongo.py
"""
import argparse
import json
import os
import zipfile

from pymongo import MongoClient


def main(filespath, namefilter='.json'):
    """Loop through zip files..."""

    client = MongoClient('mongo', 27017)
    db_collection = client['we1s']['Corpus'] # filespath

    os.chdir(filespath)
    count = 0
    errors = {}
    for (dirname, _dirs, files) in os.walk(filespath):
        for filename in files:
            if filename.endswith('.zip'):  # scan for zip files
                filepath = os.path.join(dirname, filename)
                # print('\n', filepath, '\n')
                source = zipfile.ZipFile(filepath, 'r')  # read zip
                for afile in source.filelist:
                    if namefilter and namefilter in afile.filename:
                        count += 1
                        # print('   ', afile.filename)
                        with source.open(afile) as f_in_zip:
                            try:
                                file_data = json.loads(f_in_zip.read().decode('utf-8'))
                                db_collection.insert(file_data)
                            except json.decoder.JSONDecodeError:
                                if 'JSONDecodeError' not in errors:
                                    errors['JSONDecodeError'] = 1
                                else:
                                    errors['JSONDecodeError'] += 1
                        # print('   ', afile.filename)
        # print('   ' + str(count))
    client.close()
    print(errors)
    print(count)


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description=__doc__)
    PARSER.add_argument('dir', nargs='?', default='',
                        help='directory tree to process')
    PARSER.add_argument('-n', '--namefilter', default='.json',
                        help='pattern for content filenames, e.g. json')
    ARGS = PARSER.parse_args()
    main(os.path.abspath(ARGS.dir), ARGS.namefilter)
