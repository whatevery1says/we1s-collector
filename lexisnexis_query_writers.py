#!/usr/bin/env python3
'''Lexis Nexis Query Writers: Produce Lexis Nexis queries from given lists of sources, ids, keywords, and filters, or from iterating over given directory
of Lexis Nexis zip files.'''

import calendar
import random
import csv
import os
import re

def year_dates(year):
    '''Returns begin and end dates for one year, starting on Jan 1 and ending Dec 31.'''
    begin_date = str(year) + '-01-01'
    end_date = str(year) + '-12-31'
    return begin_date, end_date

def month_dates(year):
    '''Returns begin and end dates for 1 month for one year, month selected randomly.'''
    month_range = list(range(1,13))
    random_month = str(random.sample(month_range, 1)).strip('[]')
    if len(random_month) < 2:
        random_month = '0' + random_month
    first_day = random_month + '-01'
    last_day = random_month + '-' + str(calendar.monthrange(begin_year, int(random_month))[1])
    begin_date = str(year) + '-' + first_day
    end_date = str(year) + '-' + last_day
    return begin_date, end_date

def create_kf_dict(keyword_list, filter_list):
    '''Returns an ordered dict of keyword strings and corresponding filters for given lists of each.
    Filter_list must be the same length as keyword_list and the filters must be in the same order as the keyword_list.'''
    keyword_filter_dict={}
    i=0
    for keyword in keyword_list:     
        keyword_filter_dict[keyword] = filter_list[i]
        i += 1
    return keyword_filter_dict


def query_existing(query_csv, data_dir, keyword_list, filter_list, 
                      begin_year, end_year, exclude_list=[''], by_year=True, by_month=False):
    '''Produce query csv for all Lexis Nexis sources in a given directory, using one or more keywords and result filters.
    Set by default to query all sources in one-year increments between given begin and end years. Can 
    configure to select one random month from each year to query for each keyword instead.'''
    name_id = {}  
    for file in os.listdir(data_dir):
        # Grab only Lexis Nexis files from given directory.
        if file.endswith('.zip') and re.match(r'^\d', file):
            # Split up filename into parts.
            file_parts = file.split('_')
            # Grab id and name.
            try:
                source_id = file_parts[0]
                name = file_parts[1]
            except IndexError as err:
                print(file)
            # Create name_id dict and add name and id to it.
            name_id[name] = source_id
    with open(query_csv, 'w') as qf:
        query_writer = csv.writer(qf, delimiter = ',')
        query_writer.writerow(['source_title', 'source_id', 'keyword_string', 'begin_date', 'end_date', 'result_filter'])
        year_range = list(range(begin_year, end_year+1))
        for year in year_range:
            if by_year == True:
                dates = year_dates(year)
                begin_date = dates[0]
                end_date = dates[1]
                keyword_filter_dict = create_kf_dict(keyword_list, filter_list)
                for k,v in keyword_filter_dict.items():
                    keyword_string = k
                    result_filter = v
                    for k,v in name_id.items():
                        query_writer.writerow([k, v, keyword_string, begin_date, end_date, result_filter])
            if by_month == True:
                keyword_filter_dict = create_kf_dict(keyword_list, filter_list)
                for k,v in keyword_filter_dict.items():
                    keyword_string = k
                    result_filter = v
                    dates = month_dates(year)
                    begin_date = dates[0]
                    end_date = dates[1]
                    for k,v in name_id.items():
                        query_writer.writerow([k, v, keyword_string, begin_date, end_date, result_filter])


def query_new(query_csv, source_file, keyword_list, filter_list, begin_year, end_year, 
              by_year=True, by_month=False):
    '''Produce a Lexis Nexis query from provided source names, index numbers, dates, keywords, and result filters.
    Source_file must be txt file with the following format (one source per line): 
        source_name,source_id.
    Set by default to query all given sources in one-year increments between given begin and end years. Can 
    configure to select one random month from each year to query for each keyword instead.'''
    name_id = {}  
    with open(source_file, 'r') as sf:
        for row in sf:
            # Split source_file on the comma separating name from source id.
            source_parts = row.strip().split(',')
            name = source_parts[0]
            # Remove special characters, spaces, and punctuation from source name, lowercase name.
            name = re.sub('\W+','', name).lower()
            # Grab source id.
            source_id = source_parts[1]
            # Create name_id dict and add name and id to it.
            name_id[name] = source_id
    with open(query_csv, 'w') as qf:
        query_writer = csv.writer(qf, delimiter = ',')
        query_writer.writerow(['source_title', 'source_id', 'keyword_string', 'begin_date', 'end_date', 'result_filter'])
        year_range = list(range(begin_year, end_year+1))
        for year in year_range:
            if by_year == True:
                dates = year_dates(year)
                begin_date = dates[0]
                end_date = dates[1]
                keyword_filter_dict = create_kf_dict(keyword_list, filter_list)
                for k,v in keyword_filter_dict.items():
                    keyword_string = k
                    result_filter = v
                    for k,v in name_id.items():
                        query_writer.writerow([k, v, keyword_string, begin_date, end_date, result_filter])
            if by_month == True:
                keyword_filter_dict = create_kf_dict(keyword_list, filter_list)
                for k,v in keyword_filter_dict.items():
                    keyword_string = k
                    result_filter = v
                    dates = month_dates(year)
                    begin_date = dates[0]
                    end_date = dates[1]
                    for k,v in name_id.items():
                        query_writer.writerow([k, v, keyword_string, begin_date, end_date, result_filter])

### CONFIGURATION: See below for how to configure code -- no command line interface
## Implement query_existing.

# Loop over all zips in humanities-keywords and grab source names that aren't on top newspaper list for creating
# LN queries.

# top_us_newspapers = '/home/jovyan/write/dev/top-us-newspapers.txt'
# query_csv = 'queries-existing-test.csv'
# data_dir = '/home/jovyan/data/query-test'
# keyword_list = ['person AND NOT humanities','good AND NOT humanities','say AND NOT humanities']
# # filter_list must be the same length as keyword_list and the filters wanted for each keyword should appear in the order
# # of the keywords.
# filter_list = ['humanities','humanities','humanities']
# begin_year = 2016
# end_year = 2018
# exclude_list = []

# # By year
# query_existing(query_csv, data_dir, keyword_list, filter_list, begin_year, end_year, exclude_list)
# # By month
# query_existing(query_csv, data_dir, keyword_list, filter_list, begin_year, end_year, exclude_list, 
#                  by_year=False, by_month=True)

## Implement query_new.

# source_file = '/home/jovyan/write/dev/test-source-file.txt'
# query_csv = 'queries-test.csv'
# keyword_list = ['bodypluralhumanitieshleadpluralhumanities','liberal arts','the arts']
# filter_list = ['humanities','liberal arts','the arts']
# begin_year = 2012
# end_year = 2018

## By year
# query_new(query_csv, source_file, keyword_list, filter_list, begin_year, end_year)
## By month
# query_new(query_csv, source_file, keyword_list, filter_list, begin_year, end_year, by_year=False, by_month=True)