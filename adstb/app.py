from .models import KeyValue
import adsputils
from adsputils import get_date, setup_logging, load_config, ADSCelery, u2asc
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker




def create_app(app_name='adstb',
               local_config=None):
    """Builds and initializes the Celery application."""
    
    conf = adsputils.load_config()
    if local_config:
        conf.update(local_config)

    app = ADSTurboBeeCelery(app_name,
             broker=conf.get('CELERY_BROKER', 'pyamqp://'),
             include=conf.get('CELERY_INCLUDE', ['adstb.tasks']))

    app.init_app(conf)
    return app



class ADSTurboBeeCelery(ADSCelery):
    
    def harvest_webpage(self, url):
        """Loads a bumblebee page; it reuses js client. After the page
        has been loaded (all api requests) done, it will get the 
        outer HTML."""
        
        pass
    
    
            
