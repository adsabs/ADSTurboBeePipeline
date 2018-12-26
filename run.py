#!/usr/bin/env python
"""

Main script for controlling the adstb
"""

__author__ = ''
__maintainer__ = ''
__copyright__ = 'Copyright 2016'
__version__ = '1.0'
__email__ = 'ads@cfa.harvard.edu'
__status__ = 'Production'
__license__ = 'MIT'

import sys
import time
import argparse
from adstb import tasks
from adsmsg import TurboBeeMsg
import json

app = tasks.app

def harvest_by_query(query, queue='harvest-bumblebee', 
                     tmpl='https://devapi.adsabs.harvard.edu/#abs/%(bibcode)s/abstract', 
                     **kwargs):
    """
    Given a SOLR query, it will harvest ALL bibcodes and submit
    them for processing. 
    
    :param: query - json encoded query string
    :param: queue - where to send the claims
    :param: tmpl - (str) url template for generating the final target URL (that will
            be harvested)
    
    :return: no return
    """
    params = json.loads(query)
    
    app.logger.info('Loading all records for: {0} from: {1}'.format(params, app.conf.get('SEARCH_ENDPOINT')))
    url = app.conf.get('SEARCH_ENDPOINT', 'https://api.adsabs.harvard.edu/v1/search/query')
    
    # reuse the http client with keep-alive connections
    client = app._client
    
    # that's all we care for
    params['fl'] = 'bibcode'
    
    if 'sort' not in params:
        app.logger.info('Setting default sort by read_count desc')
        params['sort'] = 'read_count desc'
    
    rows = 1000
    if 'rows' in params:
        rows = params['rows']
    
    def query(start, rows=1000):
        params['start'] = start
        params['rows'] = rows
        r = client.get(url, params=params)
        return start+rows, r.json()
    
    def submit(bibcode):
        msg = TurboBeeMsg(target=tmpl % {'bibcode': bibcode})
        tasks.task_harvest_bumblebee.delay(msg)
    
    i = 0
    start = params.get('start', 0)
    while True:
        start, j = query(start)
        for b in j['response']['docs']:
            submit(b['bibcode'])
            i += 1
        if start > j['response']['numFound']:
            break
        app.logger.info('Done: {0}/{1}'.format(start, j['response']['numFound']))
        print 'Done submitting: {0}/{1}'.format(start, j['response']['numFound'])
    
        
    app.logger.info('Done submitting {0} pages.'.format(i))


    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-q',
                        '--harvest_by_query',
                        dest='harvest_by_query',
                        action='store',
                        help='Given particular SOLR query (in JSON format with all params) it will submit all bibcodes for harvesting')
    parser.add_argument('-u',
                        '--url_tmpl',
                        dest='url_tmpl',
                        action='store',
                        default='https://devapi.adsabs.harvard.edu/#abs/%(bibcode)s/abstract',
                        help='URL template for harvesting targets')
    
    args = parser.parse_args()
    

    if args.harvest_by_query:
        harvest_by_query(args.harvest_by_query, tmpl=args.url_tmpl)
        
