"""WSK utils for WE1S (WhatEvery1Says)
"""

import csv
import datetime
import json
import logging
import os
import pprint
import re
import string
import zipfile

from bs4 import BeautifulSoup
import unidecode
from wsk import WSK

import config.config as cfg

from scrub.scrub import scrub as scrubber

def date_validate(date_text, format_string='%Y-%m-%d'):
    """Validate a date string as YYYY-MM-DD format"""
    try:
        valid_date = datetime.datetime.strptime(date_text, format_string)
    except ValueError:
        return False
    return valid_date


def get_authenticated_session():
    """Authenticate with WSK server and return a session object
    for running searches. This only needs to be done once per session.
    The session object stores the token internally as auth_token
    and uses it as needed.
    """
    # initialize a WSK session, specifying email as project identifier
    session = WSK(environment=cfg.LN_ENVIRONMENT, project_id=cfg.LN_PROJECT_ID)
    # authenticate with the web service
    session.authenticate(username=cfg.LN_USERNAME,
                         password=cfg.LN_PASSWORD)
    return session


def string_cleaner(unistr):
    """Returns string in unaccented form, printable characters only,
    with sequential whitespace collapsed to single spaces.
    """
    unaccented = unidecode.unidecode(unistr)
    printonly = ''.join(filter(lambda x: x in string.printable, unaccented))
    return ' '.join(printonly.split())


def search_query(session, query_idx, qrow, bagify=True, result_filter='',
                 outpath='', zip_output=False, scrub=True):
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
    slug_full = qrow['source_id'] + '_' + slug + '_' + qrow['begin_date'] + '_' + qrow['end_date']
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
    query_result_isempty = True
    for qitem in query_result:
        if qitem:
            query_result_isempty = False
    if query_result_isempty:
        logging.info('*** search aborted: %s', slug_full)
        return
    article_filename_list = []
    if zip_output:
        zip_path_out = os.path.join(outpath, slug_full + '.zip')
        zip_out = zipfile.ZipFile(zip_path_out, 'w', zipfile.ZIP_DEFLATED)
        zip_out.writestr('README_' + slug_full, ' ')
        if result_filter:
            zip_path_out_no_exact = os.path.join(outpath, slug_full + '(no-exact-match).zip')
            zip_out_no_exact = zipfile.ZipFile(zip_path_out_no_exact, 'w', zipfile.ZIP_DEFLATED)
            zip_out_no_exact.writestr('README_' + slug_full + '(no-exact-match)', ' ')

    for group_idx, group in enumerate(query_result):
        for article_idx, article in enumerate(group):
            name = slug_full  + '_' + str(query_idx) + '_' + str(group_idx) + '_' + str(article_idx)
            article_full_text = article.pop('full_text')
            try:  # move dictionary keys
                article['title'] = article.pop('headline', "untitled")
            except KeyError as error:
                logging.info(name, 'move headline to title failed', error)
            try: # move dictionary keys
                soup = BeautifulSoup(article_full_text, 'lxml')
                all_copyright = soup.find('div', {'class': 'PUB-COPYRIGHT'})
                if not all_copyright:
                    all_copyright = soup.find('div', {'class': 'COPYRIGHT'})
                copyright_txt = ''
                for copyright in all_copyright:
                    copyright_txt = str(copyright) # I don't know why the text isn't already a string, but it isn't, so have to make it one.
                    copyright_txt = re.sub('Copyright [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f] ', '', copyright_txt)
                article['copyright'] = copyright_txt
            except KeyError as error:
                logging.info(name, 'copyright info failed', error)      
            try:  # move dictionary keys
                body_divs = soup.find_all("div", {"class":"BODY"})
                txt = ''
                for body_div in body_divs:
                    txt = txt + body_div.get_text(separator=u' ')
                txt = string_cleaner(txt)
                if scrub:
                    article['content-unscrubbed'] = txt
                    txt = scrubber(txt)
                if bagify:
                    txt = ' '.join(sorted(txt.split(' '), key=str.lower))
                    article.pop('content-unscrubbed')
                    # if content_raw delete content_raw
                article['content'] = txt
            except (KeyError, TypeError) as error:
                logging.info(name, 'clean contents failed', error)
            try: # university wire title pre 2007
                university_wire_title = re.search('\\(C\\) ([0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) (.+) via U-WIRE', txt)
                if university_wire_title:
                        university_wire_title = university_wire_title.group(2)
                        article['pub'] = university_wire_title 
            except (KeyError, TypeError) as error:
                logging.info(name, 'no university wire title', error)
            try:  # add dictionary keys
                article['name'] = name
                article['namespace'] = "we1sv2.0"
                article['metapath'] = "Corpus," + slug_full + ",RawData"
                article['database'] = "LexisNexis"
            except (KeyError, TypeError) as error:
                logging.info(name, 'add keys failed', error)
            logging.debug(pprint.pformat(article))
            try:
                if result_filter and not re.search(result_filter,
                                                   article['content'], re.IGNORECASE):
                    article_filename = str(qrow['source_id']) + '_' + name + '(no-exact-match).json'
                    article_xml_filename = str(qrow['source_id']) + '_' + name + '(no-exact-match).xml'
                    if zip_output:
                        zip_map = zip_out_no_exact
                        zip_map.writestr(article_filename, json.dumps(article, indent=2))
                        zip_map.writestr(article_xml_filename, article_full_text)
                    else:
                        article_filepath = os.path.join(outpath, article_filename)
                        with open(article_filepath, 'w') as outfile:
                            json.dump(article, outfile, indent=2)
                        article_filename_list.append(article_filename)
                else:
                    article_filename = str(qrow['source_id']) + '_' + name + '.json'
                    article_xml_filename = str(qrow['source_id']) + '_' + name + '.xml'
                    if zip_output:
                        zip_map = zip_out
                        zip_map.writestr(article_filename, json.dumps(article, indent=2))
                        zip_map.writestr(article_xml_filename, article_full_text)
                    else:
                        article_filepath = os.path.join(outpath, article_filename)
                        with open(article_filepath, 'w') as outfile:
                            json.dump(article, outfile, indent=2)
                        article_filename_list.append(article_filename)

            except (OSError, TypeError) as error:
                logging.info(name, 'JSON write failed', error)
    if zip_output:
        zip_out.close()
        if result_filter:
            zip_out_no_exact.close()


def search_querylist(session, fname='queries.csv', bagify=True, outpath='', zip_output=False, scrub=True):
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
            begin = date_validate(row['begin_date'].strip(), format_string='%Y-%m-%d')
            end = date_validate(row['end_date'].strip(), format_string='%Y-%m-%d')
            if not begin:
                logging.info('Invalid date %s; skip query row: %s',
                             row['begin_date'], query_idx)
                continue
            elif not end:
                logging.info('Invalid date %s; skip query row: %s',
                             row['end_date'], query_idx)
                continue
            elif begin > end:
                logging.info('Begin date after end: %s, %s; skip query row: %s',
                             row['begin_date'], row['end_date'], query_idx)
            else:
                search_query(session=session,
                             query_idx=query_idx,
                             qrow={'source_title':row['source_title'],
                                   'source_id':row['source_id'],
                                   'keyword_string':row['keyword_string'],
                                   'begin_date':row['begin_date'].strip(),
                                   'end_date':row['end_date'].strip()
                                  },
                             result_filter=row['result_filter'],
                             bagify=bagify,
                             outpath=outpath,
                             zip_output=zip_output,
                             scrub=scrub
                            )


STARTTIME = datetime.datetime.now().strftime('%Y%m%d-%H%m%S')
HANDLERS = [logging.FileHandler(filename='wsk-' + STARTTIME + '.log',
                                mode='a', delay=True),
            logging.StreamHandler()]
logging.basicConfig(datefmt='%m/%d/%Y %I:%M:%S %p',
                    format='%(asctime)s %(message)s',
                    handlers=HANDLERS,
                    level=logging.INFO)

if __name__ == "__main__":
    MY_SESSION = get_authenticated_session()
    search_querylist(MY_SESSION, 'queries.csv', bagify=False, zip_output=True, scrub=True)
    logging.info("done\n\n")
