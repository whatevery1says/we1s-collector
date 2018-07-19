#!/usr/bin/env python3
"""WE1S Query Expander: Expand multi-year ranges in queries.csv into valid query rows.
"""
import csv
import pprint
import string


def expand_querylist(fname='queries.csv', fout='queries-expanded.csv'):
    """For a list of queries in csv format, expand queries for which
    the begin_date is two years joined by ... into multiple rows
    of year queries, pass through others unchanged. For example:

        source_title,source_id,keyword_string,begin_date,end_date
        Chicago Daily Herald,163823,liberal arts,1990-01-01,1990-02-01
        Chicago Daily Herald,163823,liberal arts,2000...2003,
        Chicago Daily Herald,163823,liberal arts,2010-01-01,2010-02-01

    ...here the middle row is expanded to three rows:

        source_title,source_id,keyword_string,begin_date,end_date
        Chicago Daily Herald,163823,liberal arts,1990-01-01,1990-02-01
        Chicago Daily Herald,163823,liberal arts,2000-01-01,2000-12-31
        Chicago Daily Herald,163823,liberal arts,2001-01-01,2001-12-31
        Chicago Daily Herald,163823,liberal arts,2002-01-01,2002-12-31
        Chicago Daily Herald,163823,liberal arts,2002-01-01,2003-12-31
        Chicago Daily Herald,163823,liberal arts,2010-01-01,2010-02-01
    """
    queryrows = []
    with open(fname, 'r') as csvfile:
        querydict = csv.DictReader(csvfile, delimiter=',')
        queryrows.append(querydict.fieldnames)
        for query_idx, row in enumerate(querydict):
            qrow = {'source_title':row['source_title'],
                    'source_id':row['source_id'],
                    'keyword_string':row['keyword_string'],
                    'begin_date':row['begin_date'],
                    'end_date':row['end_date']
                    }
            if '...' in row['begin_date'] and not row['end_date']:
                terms = [int(x) for x in row['begin_date'].split('...')]
                for year in range(terms[0], terms[1]+1):
                    queryrows.append([row['source_title'],
                                      row['source_id'],
                                      row['keyword_string'],
                                      str(year)+'-01-01',
                                      str(year)+'-12-31'])
            else:
                queryrows.append([row['source_title'],
                                  row['source_id'],
                                  row['keyword_string'],
                                  row['begin_date'],
                                  row['end_date']])
    pprint.pprint(queryrows)
    with open(fout, 'w') as outfile:
        csvwriter = csv.writer(outfile, delimiter=',')
        for row in queryrows:
            csvwriter.writerow(row)


if __name__ == "__main__":
    expand_querylist()
