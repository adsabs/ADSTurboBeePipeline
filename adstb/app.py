from .models import KeyValue
import adsputils
from adsputils import get_date, setup_logging, load_config, ADSCelery, u2asc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

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
        
        # update tiemstamps
        message.set_value(html, message.ContentType.html)
        message.updated = message.get_timestamp()
        message.expires.seconds = message.updated.seconds + self.conf.get('BBB_EXPIRATION_SECS', 60*60*24) # 24h later
        message.eol.seconds = message.updated.seconds + self.conf.get('BBB_EOL_SECS', 60*60*24*90) # 3 months later
        
        return True
    
    
    def _load_url(self, url):
        pass


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
        
        
