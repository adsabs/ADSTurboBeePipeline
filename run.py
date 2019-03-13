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
import argparse
import time
from adstb import tasks
from adsmsg import TurboBeeMsg
import json
from adsputils import get_date
from adstb.models import KeyValue

app = tasks.app

def harvest_by_query(query, queue='static-bumblebee', 
                     tmpl='https://dev.adsabs.harvard.edu/#abs/%(bibcode)s/abstract', 
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
        if queue == 'harvest-bumblebee':
            tasks.task_harvest_bumblebee.delay(msg)
        elif queue == 'static-bumblebee':
            tasks.task_static_bumblebee.delay(msg)
        else:
            raise Exception('Unknown target: %s' % queue)
        
    
    i = 0
    start = params.get('start', 0)
    while True:
        try:
            start, j = query(start)
            for b in j['response']['docs']:
                submit(b['bibcode'])
                i += 1
            if start > j['response']['numFound']:
                break
            app.logger.info('Done: {0}/{1}'.format(start, j['response']['numFound']))
            print 'Done submitting: {0}/{1}'.format(start, j['response']['numFound'])
        except Exception, e:
            print 'Exception', str(e)
    
        
    app.logger.info('Done submitting {0} pages.'.format(i))


def harvest_by_null(queue='priority-bumblebee', 
                    max_num=-1,
                    **kwargs):
    """
    Given a SOLR query, it will harvest ALL rows that have empty
    timestamp (entries, that should be built).
    
    :param: queue - where to send the claims
    
    :return: no return
    """
    
    url = app.conf.get('STORE_SEARCH_ENDPOINT', 'https://api.adsabs.harvard.edu/v1/store/search')
    
    # reuse the http client with keep-alive connections
    client = app._client
    params = {'null': True}
    
    
    
    i = 0
    seen = set()
    with app.session_scope() as session:
        kv = session.query(KeyValue).filter_by(key='last.null').first()
        if kv is not None:
            last_id = kv.value
        else:
            last_id = -1 
                
    
    while True:
        r = client.get(url, params=params)
        r.raise_for_status()
        j = i
        for d in r.json():
            msg = TurboBeeMsg(target=d['target'],
                              qid=d['qid'])
            
            
            tasks.task_priority_queue.delay(msg)
            params['last_id'] = d['id']
            last_id = d['id']
            if d['id'] in seen:
                break
            seen.add(d['id'])
            i+= 1
            
            if max_num > 0 and i > max_num:
                break
        
        if j == i:
            break
        
    if i > 0:
        with app.session_scope() as session:
            kv = session.query(KeyValue).filter_by(key='last.null').first()
            if kv is None:
                kv = KeyValue(key='last.null', value=last_id)
                session.add(kv)
            else:
                kv.value = last_id
            session.commit()
    
        
    app.logger.info('Done submitting {0} pages.'.format(i))
    print i, last_id


def submit_url(url, queue='harvest-bumblebee'):    
    """Submits a specific URL for processing."""
    msg = TurboBeeMsg(target=url)
    if queue == 'harvest-bumblebee':
        tasks.task_harvest_bumblebee.delay(msg)
    elif queue == 'static-bumblebee':
        tasks.task_static_bumblebee.delay(msg)
    else:
        raise Exception('Unknown target: %s' % queue)


def print_kvs():    
    """Prints the values stored in the KeyValue table."""
    
    print 'db', app.conf.get('SQLALCHEMY_URL')
    
    print 'Key, Value from the storage:'
    print '-' * 80
    with app.session_scope() as session:
        for kv in session.query(KeyValue).order_by('key').all():
            print kv.key, kv.value


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-q',
                        '--harvest_by_query',
                        dest='harvest_by_query',
                        action='store',
                        help='Given particular SOLR query (in JSON format with all params) it will submit all bibcodes for harvesting')
    parser.add_argument('-s',
                        '--submit_url',
                        dest='submit_url',
                        action='store',
                        help='Will submit for processing particular target')
    parser.add_argument('-u',
                        '--url_tmpl',
                        dest='url_tmpl',
                        action='store',
                        default='https://dev.adsabs.harvard.edu/#abs/%(bibcode)s/abstract',
                        help='URL template for harvesting targets')
    parser.add_argument('-n',
                        '--harvest_null_objects',
                        dest='harvest_null_objects',
                        action='store_true',
                        help='Will search for rows with created=null timestamp; i.e. entries that ought to be built yet')
    
    parser.add_argument('-l',
                        '--last_id',
                        dest='last_id',
                        action='store',
                        help='The last ID to be used for fetching the next pages')
    
    parser.add_argument('-k', 
                        '--kv', 
                        dest='kv', 
                        action='store_true',
                        default=False,
                        help='Show current values of KV store')
    
    parser.add_argument('-t', 
                        '--queue', 
                        dest='queue', 
                        action='store',
                        default='static-bumblebee',
                        help='Influence where to submit a task (into what queue)')
    
    args = parser.parse_args()
    
    
    if args.kv:
        print_kvs()

    if args.harvest_by_query:
        harvest_by_query(args.harvest_by_query, tmpl=args.url_tmpl, queue=args.queue)
        
    if args.harvest_null_objects:
        harvest_by_null()
    
    if args.submit_url:
        submit_url(args.submit_url)
        
