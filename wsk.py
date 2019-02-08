from pymongo import MongoClient
from bs4 import BeautifulSoup, element
from datetime import datetime, timedelta
from dateutil import parser as dateparser
from random import random
import base64
import calendar
import copy
import json
import requests
import time
import sys

class WSK:
  def __init__(self, environment='', project_id=''):
    self.environment = environment
    self.project_id = project_id
    self.auth_token = None
    self.verbose = True
    self.session_id = calendar.timegm(time.gmtime())


  def set_db(self, dbname='wsk', uri='mongodb://localhost:27017'):
    '''
    Create a MongoDB connection
    @param {str} dbname: the name of the db to use in Mongo
    @param {str} uri: a mongodb uri that specifies the db location
    '''
    self.db = MongoClient(uri)[dbname]


  def get_url(self, service, protocol='http'):
    '''
    Get the url for a query with the appropriate protocol and environment
    @param {str} service: the service endpoint to which the query will be sent
    @returns {str}: the fully-qualified url to which the request will be made
    '''
    return protocol + '://' + self.environment + '/wsapi/v1/services/' + service


  def get_headers(self, request):
    '''
    Get the headers for a query with the right content length attribute
    @param {str} request: an XML request object to be POST'ed to the WSK server
    @returns {obj}: the headers to be used in a WSK request
    '''
    return {
      'Host': self.environment,
      'Content-Type': 'text/xml; charset=UTF-8',
      'Content-Length': str(len(request)),
      'SOAPAction': ''
    }


  def authenticate(self, username, password):
    '''
    Set the WSK's auth_token attribute by authenticating with the WSK servers
    @param {str} username: the user's WSK username
    @param {str} password: the user's WSK password
    '''
    request = '''
      <SOAP-ENV:Envelope
          xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
          SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
        <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <Authenticate xmlns="http://authenticate.authentication.services.v1.wsapi.lexisnexis.com">
            <authId>{0}</authId>
            <password>{1}</password>
          </Authenticate>
        </soap:Body>
      </SOAP-ENV:Envelope>
      '''.format(username, password)
    url = self.get_url('Authentication', protocol='https')
    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    try:
      self.auth_token = BeautifulSoup(response.text, 'lxml').find('binarysecuritytoken').string
      return self.auth_token
    except AttributeError as e:
      print(' * Authentication failure. Please verify your credentials and environment')
      print(' * url:      ', url)
      print(' * response: ', response)
      print(' * e:        ', e)
      sys.exit()


  ##
  # Browse Sources
  ##

  def get_all_sources(self):
    '''
    Get a list of the sources available to the current account. To do so, find
    all source types, then descend down the tree of folders to find all
    sources / leaf nodes. NB: Different folders have different depths one must
    descend to find sources / leaf nodes.
    '''
    # populate list of sources available to account
    sources = []
    # find the top order folder
    root_folders = self.browse_sources()
    # use the first source grouping folder to recurse through the folder hierarchy
    sub_folders = self.browse_sources(root_folders[0]['folder_id'])
    # descend into all sub folders and add any newly discovered sub folders to this list
    while sub_folders:
      sub_folder = sub_folders.pop(0)
      print(' * fetching sources in', sub_folder)
      # some results will contain parent folders, others contain source / leaf nodes
      result = self.browse_sources(sub_folder['folder_id'])
      if 'source_id' not in result[0]:
        sub_folders += result
      else:
        sources += result
    return sources


  def browse_sources(self, folder_id=''):
    '''
    Query for the sources to which the account has access. LexisNexis organizes
    sources into "folders". Each folder contains subfolders, which contain source
    information. To find all sources to which your account has access, one can choose
    a folder_id, find all subfolders, then find all sources within each of those
    subfolders and use the resulting set of sources.
    @param {str} folder_id: The high order folder to search for sources. If a
      folder_id is not provided, the query result will contain a list of available
      folder names and folder ids.
    @returns {obj} If the user did not provide a folder_id, obj will be a list
      of objects, where each object has name and folder_id attributes that describe
      a top-level folder.

      If the user provided a folder_id and that folder_id has children folders, obj
      will contain a list of objects, where each object has name and folder_id attributes
      that describe a subfolder within the queried folder_id.

      If the user provided a folder_id and that folder_id contains a list of sources,
      obj will contain a list of objects where each object contains source_id,
      type, name, and other metadata attributes.
    '''
    # assemble the folder argument to be passed to the soap request
    folder_arg = '<folderId>{0}</folderId>'.format(folder_id) if folder_id else ''
    # assemble the browse source query
    request = '''
    <SOAP-ENV:Envelope
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
        SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
      <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <BrowseSources xmlns="http://browsesources.source.services.v1.wsapi.lexisnexis.com">
          <locale>en-US</locale>
          <binarySecurityToken>{0}</binarySecurityToken>
          {1}
        </BrowseSources>
      </soap:Body>
    </SOAP-ENV:Envelope>
    '''.format(self.auth_token, folder_arg)
    url = self.get_url('Source')
    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    soup = BeautifulSoup(response.text, 'lxml')
    results = []

    # parse out the sources identified for this query
    # nb: sources have differnet namespace prefixes
    sources = []
    for i in soup.find('sourcelist').findChildren():
      if 'source' in i.name:
        if 'sourceid' not in i.name and 'premiumsource' not in i.name:
          sources.append(i)

    # case where query result contains sources
    if sources:
      for i in sources:
        results.append({
          'name': find_tag_by_name(i, 'name').get_text(),
          'source_id': int(find_tag_by_name(i, 'sourceid').get_text()),
          'type': find_tag_by_name(i, 'type').get_text(),
          'premium_source': find_tag_by_name(i, 'premiumsource').get_text(),
          'has_index': bool(find_tag_by_name(i, 'hasindex').get_text()),
          'has_toc': bool(find_tag_by_name(i, 'hastoc').get_text()),
          'versionable': bool(find_tag_by_name(i, 'versionable').get_text()),
          'is_page_browsable': bool(find_tag_by_name(i, 'ispagebrowsable').get_text()),
        })

    # case where query result contains folders
    else:
      for i in soup.find_all('folder'):
        results.append({
          'name': i.find('name').get_text(),
          'folder_id': i.find('folderid').get_text()
        })

    return results


  ##
  # Search Sources
  ##

  def search_sources(self, query):
    '''
    @param: {str} query: a query for sources
    @returns: {arr}: a list of source metadata objects that match the query
    '''
    request = '''
      <SOAP-ENV:Envelope
          xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
          SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
        <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <SearchSources xmlns="http://searchsources.source.services.v1.wsapi.lexisnexis.com">
            <locale>en-US</locale>
            <binarySecurityToken>{0}</binarySecurityToken>
            <partialSourceName>{1}</partialSourceName>
          </SearchSources>
        </soap:Body>
      </SOAP-ENV:Envelope>
      '''.format(self.auth_token, query)

    url = self.get_url('Source')
    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    soup = BeautifulSoup(response.text, 'xml')
    sources = []
    for i in soup.find_all('source'):
      combinable_list = []
      for j in i.find_all('combinability'):
        combinable_list.append(j.text)
      sources.append({
        'name': i.find('name').text,
        'source_id': int(i.find('sourceId').text),
        'type': i.find('type').text,
        'premium_source': bool(i.find('premiumSource').text),
        'has_index': bool(i.find('hasIndex').text),
        'versionable': bool(i.find('versionable').text),
        'is_page_browsable': bool(i.find('isPageBrowsable').text),
        'combinability': combinable_list
      })
    return sources


  ##
  # Get Source Details
  ##

  def get_source_details(self, source_id):
    '''
    @param: {int} source_id: a source id for which details are requested
    @returns: {arr}: a list of objects describing titles in the source id
    '''
    request = '''
      <SOAP-ENV:Envelope
          xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
          SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
        <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <GetSourceDetails xmlns="http://getsourcedetails.source.services.v1.wsapi.lexisnexis.com">
            <binarySecurityToken>{0}</binarySecurityToken>
            <sourceId>{1}</sourceId>
            <includeSourceElement>true</includeSourceElement>
          </GetSourceDetails>
        </soap:Body>
      </SOAP-ENV:Envelope>
      '''.format(self.auth_token, source_id)

    url = self.get_url('Source')
    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    soup = BeautifulSoup(response.text, 'lxml')
    sources = []
    for i in soup.find('sourceguidelist').find_all('sourceguide'):
      sources.append(self.parse_source_details(i))
    return sources


  def parse_source_details(self, soup):
    '''
    @param: {BeautifulSoup} soup: contains the sourceguide tag from a
      get_source_details() query
    @returns: {obj}: an object that details the titles in the current source
    '''
    source = base64.b64decode(soup.string)
    source_soup = BeautifulSoup(source, 'lxml')
    exclusions = source_soup.find('div', {'EXCLUSIONS'}).find_all('p')[3]
    return dict({
      'source_name': source_soup.find('div', {'class': 'PUBLICATION-NAME'}).text,
      'file_name': source_soup.find('div', {'class': 'FILE-NAME'}).text,
      'content_summary': source_soup.find('div', {'class': 'CONTENT-SUMMARY'}).text,
      'full_text': self.split_on_br(source_soup.find('div', {'FULL-TEXT'})),
      'selected_text': self.split_on_br(source_soup.find('div', {'SELECTED-TEXT'})),
      'also_contains': self.split_on_br(source_soup.find('div', {'ALSO-CONTAINS'})),
      'exclusions': self.split_on_br(exclusions),
    })


  def split_on_br(self, soup):
    '''
    @param: {BeautifulSoup}: contains a list of elements separated by <br/> tags
    @returns: {arr}: a list of the elements in the soup
    '''
    elems = []
    for i in soup.contents:
      if getattr(i, 'name', None) != 'br':
        if type(i) is element.Tag:
          elems.append(i.string)
        else:
          elems.append(i)
    return elems


  ##
  # Search Method
  ##

  def search(self,
    query,
    source_id,
    get_text=True,
    start_date='2017-12-01',
    end_date='2017-12-02',
    return_results=False,
    save_results=True,
    yield_results=False,
    time_delta=30):
    '''
    Run a full query for the user, fetching all doc metadata and content

    @param: {str} query: the user's document query phrase
    @param: {int} source_id: the source id to which queries will be addressed
    @param: {str} start_date: the starting query date in string format
    @param: {str} end_date: the ending query date in string format
    @param: {bool} yield_results: stream results to the parent function
    @param: {bool} return_results: return matches to the parent function
    @param: {bool} store_results: save matches to mongo
    @param: {bool} get_text: fetch full text content for each match
    @param: {bool} time_delta: time stride in days
    @returns: {obj} an object with metadata describing search results data
    '''
    user_results = []  # results to return to user
    per_page = 10      # results per page
    start_date, end_date = self.get_search_dates(start_date, end_date)
    query_start_date = start_date
    query_end_date = start_date + timedelta(days=time_delta)
    more_days_to_query = True
    more_pages_to_query = True

    while more_days_to_query:
      # initialize pagination params for the new page
      # query_begin and end marks the `begin` and `end` XML values for a query
      query_begin = 1
      query_end = per_page
      end = float('inf')

      while more_pages_to_query or more_days_to_query:
        start_date_str = self.date_to_string(query_start_date)
        end_date_str = self.date_to_string(query_end_date)
        query_result = self.run_search(query, source_id, begin=query_begin,
            end=query_end, start_date=start_date_str, end_date=end_date_str,
            save_results=save_results, get_text=get_text)

        # case where query returned no results
        if query_result['total_matches'] == 0:
          more_pages_to_query = False
          # case where there are more dates to cover
          if query_end_date < end_date:
            # slide the date window forward and reset the pagination values
            query_start_date = query_start_date + timedelta(days=time_delta)
            query_end_date = query_start_date + timedelta(days=time_delta)
            query_begin = 1
            query_end = per_page
          else:
            more_days_to_query = False

        # only append to results in RAM if necessary
        if return_results: user_results += query_result['results']
        if yield_results: yield query_result['results']

        # update the total number of matches to fetch (=inf on error & start)
        end = float(query_result['total_matches'])

        # validate whether the request succeeded or errored
        if query_result['status_code'] == 200:
          # continue paginating over responses for the current date range
          if query_end < end:
            query_begin += per_page
            query_end += per_page
          # pagination is done, check whether to slide the date window forward
          else:
            more_pages_to_query = False
            # case where there are more dates to cover
            if query_end_date < end_date:
              # slide the date window forward and reset the pagination values
              query_start_date = query_start_date + timedelta(days=time_delta)
              query_end_date = query_start_date + timedelta(days=time_delta)
              query_begin = 1
              query_end = per_page
              # also potentially increment the time delta for longer strides
              if query_result['total_matches'] < (per_page/2): time_delta += 1
            # we're done!
            else: more_days_to_query = False
        # the request failed, so decrement time_delta or flail
        else:
          if time_delta > 1:
            time_delta -= 1
          else: print(' * Abort!')
    if return_results:
      yield user_results


  def run_search(self,
    query,
    source_id,
    begin=1,
    end=10,
    start_date='2017-12-01',
    end_date='2017-12-02',
    save_results=True,
    get_text=True):
    '''
    Method that actually submits search requests. Called from self.search(),
    which controls the logic that constructs the individual searches
    @param: {str} query: the user's document query phrase
    @param: {int} source_id: the source id to which queries will be addressed
    @param: {int} begin: the starting result number to return
    @param: {int} end: the ending result number to return
    @param: {str} start_date: the starting query date in string format
    @param: {str} end_date: the ending query date in string format
    @param: {bool} save_results: save matches to mongo
    @param: {bool} get_text: fetch full text content for each match
    @returns: {obj} an object with metadata describing search results data
    '''
    print(' * querying for', query, source_id, begin, end, start_date, end_date)

    request = '''
      <SOAP-ENV:Envelope
          xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
          SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
        <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <Search xmlns="http://search.search.services.v1.wsapi.lexisnexis.com">
            <binarySecurityToken>{0}</binarySecurityToken>
            <sourceInformation>
              <sourceIdList xmlns="http://common.search.services.v1.wsapi.lexisnexis.com">
                <sourceId xmlns="http://common.services.v1.wsapi.lexisnexis.com">{1}</sourceId>
              </sourceIdList>
            </sourceInformation>
            <query>{2}</query>
            <projectId>{3}</projectId>
            <searchOptions>
              <sortOrder xmlns="http://common.search.services.v1.wsapi.lexisnexis.com">Date</sortOrder>
              <dateRestriction xmlns="http://common.search.services.v1.wsapi.lexisnexis.com">
                <startDate>{4}</startDate>
                <endDate>{5}</endDate>
              </dateRestriction>
            </searchOptions>
            <retrievalOptions>
              <documentView xmlns="http://result.common.services.v1.wsapi.lexisnexis.com">Cite</documentView>
              <documentMarkup xmlns="http://result.common.services.v1.wsapi.lexisnexis.com">Display</documentMarkup>
              <documentRange xmlns="http://result.common.services.v1.wsapi.lexisnexis.com">
                <begin>{6}</begin>
                <end>{7}</end>
              </documentRange>
            </retrievalOptions>
          </Search>
        </soap:Body>
      </SOAP-ENV:Envelope>
      '''.format(self.auth_token, source_id, query, self.project_id,
          start_date, end_date, begin, end)
    url = self.get_url('Search')

    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    soup = BeautifulSoup(response.text, 'lxml')
    result_packet = {}
    result_packet['status_code'] = response.status_code
    result_packet['total_matches'] = 0
    result_packet['results'] = []

    try:
      result_count_tag = find_tag_by_name(soup, 'documentsfound')
      result_packet['total_matches'] = int(result_count_tag.get_text())
    except AttributeError:
      result_packet['total_matches'] = 0

    if (result_packet['total_matches'] == 0) or (result_packet['status_code'] != 200):
      return result_packet
    else:
      result_packet['results'] = self.get_documents(soup, get_text)

    if save_results: self.save_results(result_packet['results'])

    return result_packet


  def save_results(self, results):
    '''
    Save all search results to the database
    @param: {arr} results: a list of search result objects
    '''
    if not self.db:
      raise Exception('Please call set_db() before saving records')
      return

    if not results: return

    composed_results = []
    copied = copy.deepcopy(results)
    for i in copied:
      i['session_id'] = self.session_id
      i['project_id'] = self.project_id
      composed_results.append(i)
    self.db.results.insert_many(composed_results)


  def get_search_dates(self, start_date, end_date):
    '''
    @param {str} start_date: the starting date for the query: '2017-12-01'
    @param {str} end_date: the ending date for the query: '2017-12-02'
    @returns datetime, datetime: the start and end dates as datetime objects
    '''
    return self.string_to_date(start_date), self.string_to_date(end_date)


  def string_to_date(self, string_date):
    '''
    @param: {str} string_date: a date in string format: '2017-12-01'
    @returns: {datetime}: the input date in datetime format
    '''
    year, month, day = [int(i) for i in string_date.split('-')]
    return datetime(year, month, day)


  def date_to_string(self, datetime_date):
    '''
    @param: {datetime}: a datetime object
    @returns: {str}: the input datetime in string format: 'YYYY-MM-DD'
    '''
    return datetime_date.strftime('%Y-%m-%d')


  def get_documents(self, soup, get_text=True):
    '''
    @param: {BeautifulSoup}: the result of a search() query
    @returns: {arr}: a list of objects, each describing a match's metadata
    '''
    # create a store of processed documents
    docs = []
    # find list of document containers
    doc_containers = []
    for i in soup.findChildren():
      if 'documentcontainer' in i.name and 'documentcontainerlist' not in i.name:
        doc_containers.append(i)
    for idx, i in enumerate(doc_containers):
      try:
        doc = Document(i).metadata
        if get_text:
          doc['full_text'] = self.get_full_text(doc['doc_id'])
        docs.append(doc)
      except Exception as exc:
        print(' ! could not process doc', idx, exc)
    return docs

  ##
  # Get Full Text Content
  ##

  def get_full_text(self, document_id):
    '''
    @param: {int}: a document's id number
    @returns:
    '''
    request = '''
      <SOAP-ENV:Envelope
          xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
          SOAP-ENV:encodingStyle= "http://schemas.xmlsoap.org/soap/encoding/">
        <soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <GetDocumentsByDocumentId xmlns="http://getdocumentsbydocumentid.retrieve.services.v1.wsapi.lexisnexis.com">
            <binarySecurityToken>{0}</binarySecurityToken>
            <documentIdList>
              <documentId>{1}</documentId>
            </documentIdList>
            <retrievalOptions>
              <documentView>FullText</documentView>
              <documentMarkup>Display</documentMarkup>
            </retrievalOptions>
          </GetDocumentsByDocumentId>
        </soap:Body>
      </SOAP-ENV:Envelope>
      '''.format(self.auth_token, document_id)

    url = self.get_url('Retrieval')
    response = requests.post(url=url, headers=self.get_headers(request), data=request)
    soup = BeautifulSoup(response.text, 'xml')
    return base64.b64decode(soup.document.text).decode('utf8')


class Document(dict):
  def __init__(self, document_soup):
    self.verbose = False
    self.include_meta = False
    self.metadata = self.format_doc(document_soup)


  def format_doc(self, soup):
    '''
    @param {BeautifulSoup} soup: contains a document from a search() query:

      <ns1:documentcontainer>
        <ns1:documentid>02A6A252C52</ns1:documentid>
        <ns1:document>PD94bWwgdmVyc2lvbj0i</ns1:document>
      </ns1:documentcontainer>

      Here the <documentid> contains the doc's id and <document> contains a
      base64 encoded representation of the doc's metadata
    @returns: {obj}: an object with metadata attributes from the decoded doc
    '''
    formatted = {}
    decoded = base64.b64decode(soup.find('ns1:document').get_text())
    doc_soup = BeautifulSoup(decoded, 'lxml')
    if self.include_meta:
      for i in doc_soup.find_all('meta'):
        try:
          formatted[ i['name'] ] = i['content']
        except Exception as exc:
          if self.verbose: print(' ! error formatting doc', i['name'], exc)

    formatted['doc_id'] = soup.find('ns1:documentid').get_text()
    formatted['headline'] = self.get_doc_headline(doc_soup)
    formatted['attachment_id'] = self.get_doc_attachment_id(doc_soup)
    formatted['pub'] = self.get_doc_pub(doc_soup)
    formatted['pub_date'] = self.get_doc_pub_date(doc_soup)
    formatted['length'] = self.get_doc_length(doc_soup)
    formatted['section'] = self.get_doc_section(doc_soup)
    formatted['author'] = self.get_doc_author(doc_soup)
    return formatted


  ##
  # Document attribute accessors
  ##

  def get_doc_headline(self, soup):
    '''
    @param {BeautifulSoup} soup: the soup from a documentcontainer tag
    @returns {str} the headline from a document
    '''
    try:
      headline = soup.find('div', {'class': 'HEADLINE'}).string
      if headline:
      	return headline
      headline = soup.find('h1').string
      if headline:
          return headline
      return ''
    except Exception as exc:
      if self.verbose: print(' ! error parsing headline', exc)
      return ''


  def get_doc_attachment_id(self, soup):
    '''
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the attachmentId attribute of a document
    '''
    try:
      attachment_node = soup.find('span', {'class': 'attachmentId'})['id']
      return attachment_node if attachment_node else ''
    except Exception as exc:
      if self.verbose: print(' ! error parsing doc_attachment', exc)
      return ''


  def get_doc_pub(self, soup, default_name='No pub name'):
    '''
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the publication attribute of a document
    '''
    try:
      pub = soup.find('meta', {'name': 'sourceName'})['content']
      if pub:
        return pub
      pub = soup.find('div', {'class': 'PUB'}).string
      if pub:
        return pub
      return default_name
    except Exception as exc:
      if self.verbose: print(' ! error parsing doc_pub', exc)
      return ''


  def get_doc_pub_date(self, soup):
    '''
    Parses different human-readable date formats dynamically,
    e.g.:
        January 3, 2017 Tuesday 5:00 PM GMT
    and returns a date in UTC+Z format using the format,
    e.g.:
        2017-01-03T17:00:00Z
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the pub date attribute from a document
    '''
    bad_date = '1900-01-01T00:00:00Z'
    try:
      soup_date = soup.find('div', {'class': 'PUB-DATE'})
      if not soup_date:
          soup_date = soup.find('div', {'class': 'DATE'})
          print("DATE")
      date_str = soup_date.get_text()
      print("date_str: ", date_str)
      date = ''
      while not date:
          try:
              date = dateparser.parse(date_str)
              print(' parsed: ', date)
          except Exception as exc:
              print(' ! error parsing doc_pub_date', exc)
              date_str = ' '.join(date_str.split(' ')[:-1])
      date_out = date.strftime('%Y-%m-%dT%H:%M:%SZ')
      if not date_out:
          date_out = bad_date
      print(date_out)
      return date_out
    except Exception as exc:
      self.verbose = True
      if self.verbose: print(' ! error parsing doc_pub_date', exc)
      return ''


  def get_doc_length(self, soup):
    '''
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the length attribute of a document
    '''
    try:
      length = soup.find('div', {'class': 'LENGTH'}).string
      length = length.replace(' words', '')
      return length if length else ''
    except Exception as exc:
      if self.verbose: print(' ! error parsing doc_length', exc)
      return ''
      
  
  def get_doc_section(self, soup):
    '''
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the newspaper section attribute of a document
    '''
    try: 
      section = soup.find('div', {'class': 'SECTION'}).string 
      if section:
        return section
    except Exception as exc:
      # for some reason this only works if this option is brought down to the except portion of try except.
      # compare to get_doc_pub, for instance, which works without this structure.
      # but in this case, if soup fails to find anything in <div class = "SECTION">, it craps out and goes to except, returning "No pub section."
      # moving the second option of where to find section info into except fixes this.
      section = soup.find('div', {'class': 'SECTION-INFO'}).string
      if section:
        return section
      else:
        if self.verbose: print(' ! error parsing doc_section', exc)
        return 'No pub section'
  

  def get_doc_author(self, soup):
    '''
    @param {BeautifulSoup} soup: a documentcontainer tag
    @returns {str}: the author attribute of a document
    '''
    try:
      author = soup.find('div', {'class': 'BYLINE'}).string
      author = author.replace('By ', '')
      if author:
        return author
    except Exception as exc:
      if self.verbose: print(' ! error parsing doc_author', exc)
      return ''
      
##
# Helpers
##

def find_tag_by_name(soup, tag_name):
  '''
  Given a BeautifulSoup object and a tag name, return the first
  tag whose name contains `tag_name`
  @param {BeautifulSoup} soup: a BeautifulSoup object
  @param {str} tag_name: the name of the tag to find
  @returns {BeautifulSoup} the first child whose name contains `tag_name`
  '''
  for tag in soup.findChildren():
    if tag_name in tag.name:
      return tag
  return None