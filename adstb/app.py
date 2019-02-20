from .models import KeyValue
import adsputils
from adsputils import get_date, setup_logging, load_config, ADSCelery, u2asc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from adstb.exceptions import InvalidContent
import time
from requests.exceptions import ConnectionError

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import urlparse

import requests


def create_app(app_name='adstb',
               local_config=None):
    """Builds and initializes the Celery application."""
    
    conf = adsputils.load_config()
    if local_config:
        conf.update(local_config)

    app = ADSTurboBeeCelery(app_name,
             broker=conf.get('CELERY_BROKER', 'pyamqp://'),
             include=conf.get('CELERY_INCLUDE', ['adstb.tasks']))

    return app



# valid url patterns in BBB
bbb_paths = ('search', 'abs', 'user', 'index', 'execute-query')

class ADSTurboBeeCelery(ADSCelery):
    
    def __init__(self, *args, **kwargs):
        ADSCelery.__init__(self, *args, **kwargs)
    
        self._client = requests.Session()
        self._client.headers.update({'Authorization': 'Bearer:{}'.format(self.conf['API_TOKEN'])})
        self._err_counter = 0
    
    def _pick_bbb_url(self, url):
        """This method will return a hash version of an url;
        and the push-state version of the URL; we'll always
        save the push-state because that is what the webserver
        can see."""
        
        if '#' in url:
            for x in bbb_paths:
                k = '#' + x + '/'
                if k in url:
                    return url, url.replace(k, x + '/')
        else:
            for x in bbb_paths:
                k = x + '/'
                if k in url:
                    return url.replace(k, '#' + x + '/'), url  
            
        # default, do nothing
        return url, url
                
        
    def harvest_webpage(self, message):
        """Loads a bumblebee page; it reuses js client. After the page
        has been loaded (all api requests) done, it will get the 
        outer HTML."""
        
        if not message.target:
            return None
        
        url = message.target
        if not (url.startswith('http') or url.startswith('//')):
            bibcode = self.extract_bibcode(message.target)
            if bibcode:
                url = self.conf.get('BBB_ABS_PAGE', 'https://ui.adsabs.harvard.edu/abs/{}/abstract').format(bibcode)
            else:
                raise Exception('Sorry, dont know how to load webpage: {}'.format(message.target))
        
        
        bbb_url, official_url = self._pick_bbb_url(url)
        self.logger.info('Going to harvest: %s (and save as: %s)', bbb_url, official_url)
        html = self._load_url(bbb_url)
        message.target = official_url
        
        
        # update tiemstamps
        message.set_value(html, message.ContentType.html)
        message.updated = message.get_timestamp()
        message.expires.seconds = message.updated.seconds + self.conf.get('BBB_EXPIRATION_SECS', 60*60*24) # 24h later
        message.eol.seconds = message.updated.seconds + self.conf.get('BBB_EOL_SECS', 60*60*24*90) # 3 months later
        
        if not message.created.seconds:
            message.created = message.updated
        return True
    
    
    def _load_url(self, url):
        try:
            r = requests.post(self.conf.get('PUPPETEER_ENDPOINT', 'http://localhost:3001/scrape'),
                json=[url])
            r.raise_for_status()
            self._err_counter = 0
            return r.json()[url]
        except Exception, e:
            self._err_counter += 1
            raise e

    def _massage_page(self, url, html):
        
        # modify the links on the page (well, clever method could modify all links, 
        # but it might not catch scripts; so le'ts go brute force...)
        text = html[0:300].lower()
        head_start = text.index('<head')
        if head_start == -1:
            raise InvalidContent('Cannot find <head> element for: %s' % url)
        
        # find the closing bracket
        i = head_start + 1
        head_end = None
        while i < len(text):
            if text[i] == '>' and text[i-1] != '\\':
                head_end = i
                break
            i += 1

        if not head_end:
            raise InvalidContent('Cannot find closing tag of <head> element for: %s' % url)
        
        # insert base href
        b = urlparse.urlparse(url)
        base = '\n<base href="' + b.scheme + '://' + b.netloc + '" />\n'

        return html[0:head_end+1] + base + html[head_end+1:]


    def extract_bibcode(self, url_or_target):
        v = url_or_target
        if len(v) == 19:
            return v
        elif '/abs' in v:
            parts = v.split('abs/')
            if len(parts) > 1:
                return parts[1][0:19]
        else:
            return None # can't find it
        
    def update_store(self, message):
        """Delivers the message to the remote api side.
        
        :param: message - protobuf of TurboBeeMsg
        :return: qid - qid when operation succeeded
        """
        r = self._post(self.conf.get('UPDATE_ENDPOINT'), message)
        r.raise_for_status()
        return r
        
        
    def _post(self, url, messages):
        if not isinstance(messages, list):
            messages = [messages]
        out = {}
        i = 0
        for m in messages:
            clz, data = m.dump()
            out[str(i)] = data
            i += 1
        return self._client.post(url, files=out)


    def attempt_recovery(self, task, args=None, kwargs=None, einfo=None, retval=None):
        """Block if we get connection error"""
        
        if isinstance(retval, ConnectionError):
            self.logger.warn('Cannot establish connection with the crawler; blocking for %s seconds', self._err_counter**2 )
            time.sleep(self._err_counter**2)
            
        
        
