"""WSK utils for WE1S (WhatEvery1Says)
"""

import csv
import json
import logging
import pprint
import zipfile

from bs4 import BeautifulSoup
from wsk import WSK
import config.config as cfg


def get_authenticated_session():
    """Authenticate with WSK server and return a session object
    for running searches. This only needs to be done once per session.
    The session object stores the token internally as auth_token
    and uses it as needed.
    """
    # initialize a WSK session, specifying email as project identifier
    session = WSK(environment=cfg.ln_environment, project_id=cfg.ln_project_id)
    # authenticate with the web service
    session.authenticate(username=cfg.ln_username,
                         password=cfg.ln_password)
    return session


def search_query(session, query_idx, qrow, bagify=True, zip_output=False):
    """Uses a session and a query row (labeled with an arbitrary index number)
    to retrieve an article collection and cache their word lists in JSON format.
    The qrow format is a dict with keys:

        'source_title'    (e.g. Chicago Daily Herald -- not used in search)
        'source_id'       (e.g. 163823 -- the wsk source id)
        'keyword_string'  (e.g. "liberal arts")
        'begin_date'      (e.g. '2017-12-01')
        'end_date'
    """
    slug = ''.join(c for c in qrow['source_title'] if c.isalnum()).lower() + '_' + \
           ''.join(c for c in qrow['keyword_string'] if c.isalnum()).lower()
    logging.info(slug)
    query = session.search(query=qrow['keyword_string'],
                           source_id=qrow['source_id'],
                           start_date=qrow['begin_date'],
                           end_date=qrow['end_date'],
                           save_results=False,
                           return_results=False,
                           yield_results=True
                          )
    query_result = list(query)
    article_filename_list = []
    if zip_output:
        zip_path_out = qrow['source_id'] + '_' + slug + '.zip'
        zip_out = zipfile.ZipFile(zip_path_out, 'w', zipfile.ZIP_DEFLATED)

    for group_idx, group in enumerate(query_result):
        for article_idx, article in enumerate(group):
            name = slug  + '_' + str(query_idx) + '_' + str(group_idx) + '_' + str(article_idx)
            try:  # move dictionary keys
                article['title'] = article.pop('headline', "untitled")
            except KeyError as error:
                logging.info(name, 'move headline to title failed', error)
            try:  # move dictionary keys
                txt = BeautifulSoup(article.pop('full_text'), 'lxml').get_text()
                if bagify:
                    txt = ' '.join(sorted(txt.split(' '), key=str.lower))
                article['content'] = txt
            except (KeyError, TypeError) as error:
                logging.info(name, 'clean contents failed', error)
            try:  # add dictionary keys
                article['name'] = name
                article['namespace'] = "we1sv2.0"
                article['metapath'] = "Corpus," + slug + ",RawData"
            except (KeyError, TypeError) as error:
                logging.info(name, 'add keys failed', error)
            logging.debug(pprint.pformat(article))
            try:
                article_filename = str(qrow['source_id']) + '_' + name + '.json'
                if zip_output:
                    zip_out.writestr(article_filename, json.dumps(article, indent=2))
                else:
                    with open(article_filename, 'w') as outfile:
                        json.dump(article, outfile, indent=2)
                    article_filename_list.append(article_filename)
            except (OSError, TypeError) as error:
                logging.info(name, 'JSON write failed', error)
    if zip_output:
        zip_out.close()


def search_querylist(session, fname='queries.csv', bagify=True, zip_output=False):
    """For a list of queries in csv format:

        source_title,source_id,keyword_string,begin_date,end_date
        Chicago Daily Herald,163823,liberal arts,2017-01-01,2017-02-01

    Output will be saved to queries.json and per-article json files.
    The JSON format for an article is:

        {
          "name": "guardian-article1",
          "namespace": "we1sv2.0",
          "metapath": "Corpus,guardian-h,RawData",
          "title": "Research funding: are we in danger of concentrating too hard?",
          "content": "A growing obsession with funding scale risks crowding
        out institutions and stifling innovation..."
        }
    """
    with open(fname, 'r') as csvfile:
        querylist = csv.DictReader(csvfile, delimiter=',')
        for query_idx, row in enumerate(querylist):
            search_query(session=session,
                         query_idx=query_idx,
                         qrow={'source_title':row['source_title'],
                               'source_id':row['source_id'],
                               'keyword_string':row['keyword_string'],
                               'begin_date':row['begin_date'],
                               'end_date':row['end_date']
                              },
                         bagify=bagify,
                         zip_output=zip_output
                        )


HANDLERS = [logging.FileHandler(filename='wsk.log', mode='a', delay=True),
            logging.StreamHandler()]
logging.basicConfig(datefmt='%m/%d/%Y %I:%M:%S %p',
                    format='%(asctime)s %(message)s',
                    handlers=HANDLERS,
                    level=logging.INFO)

MY_SESSION = get_authenticated_session()

search_querylist(MY_SESSION, 'queries_small.csv', bagify=False, zip_output=True)

logging.info("done\n\n")