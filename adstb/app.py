from .models import KeyValue
import adsputils
from adsputils import get_date, setup_logging, load_config, ADSCelery, u2asc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from adstb.exceptions import InvalidContent

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



class ADSTurboBeeCelery(ADSCelery):
    
    def __init__(self, *args, **kwargs):
        ADSCelery.__init__(self, *args, **kwargs)
    
        self._client = requests.Session()
        self._client.headers.update({'Authorization': 'Bearer:{}'.format(self.conf['API_TOKEN'])})
        
        
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
                url = self.conf.get('BBB_ABS_PAGE', 'https://ui.adsabs.harvard.edu/abs/{}').format(bibcode)
            else:
                raise Exception('Sorry, dont know how to load webpage: {}'.format(message.target))
        
        # TODO: load the actual bbb webpage
        self.logger.info('Going to harvest: %s', url)
        html = self._load_url(message.target)
        html = self._massage_page(message.target, html)
        
        # update tiemstamps
        message.set_value(html, message.ContentType.html)
        message.updated = message.get_timestamp()
        message.expires.seconds = message.updated.seconds + self.conf.get('BBB_EXPIRATION_SECS', 60*60*24) # 24h later
        message.eol.seconds = message.updated.seconds + self.conf.get('BBB_EOL_SECS', 60*60*24*90) # 3 months later
        
        return True
    
    
    def _load_url(self, url):
        r = requests.post(self.conf.get('PUPPETEER_ENDPOINT', 'http://localhost:3001/scrape'),
            data=[url])
        r.raise_for_status()
        return r.json()[url]

    def _message_page(self, url, html):
        # make sure we were given a valid page
        if url not in html:
            self.logger.debug('%s not found in html: %s...', url, html[0:500])
            raise InvalidContent('Rejecting what was generated for: %s' % url)
        
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
        base = '\n<base href="' + b.scheme + '//' + b.netloc + '" /base>\n'

        return html[0:head_end] + base + html[head_end+1:]


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
        r.raise_for_error()
        
        
    def _post(self, url, message):
        
        clz, data = message.dump()
        return self._client.post(url, data=data)
        
        
