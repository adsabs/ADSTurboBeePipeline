import sys
import os
import json

from mock import patch
import unittest
from adstb import app, tasks
from adstb.models import Base
from adsmsg import TurboBeeMsg

class TestWorkers(unittest.TestCase):
    
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.proj_home = os.path.join(os.path.dirname(__file__), '../..')
        self._app = tasks.app
        self.app = app.create_app('test', local_config=\
            {
            'SQLALCHEMY_URL': 'sqlite:///',
                'SQLALCHEMY_ECHO': False,
                'PROJ_HOME': self.proj_home,
                'TEST_DIR': os.path.join(self.proj_home, 'adsmp/tests')
            })
        tasks.app = self.app # monkey-patch the app object
        Base.metadata.bind = self.app._session.get_bind()
        Base.metadata.create_all()
    
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        Base.metadata.drop_all()
        self.app.close_app()
        tasks.app = self._app


    def test_task_harvest_bumblebee(self):
        
        
        with patch.object(tasks.app, '_load_url', return_value = '<html><head>foo</head> 2019MNRAS.482.1872B </html>') as loader, \
            patch.object(tasks.task_output_results, 'delay') as next_task:
            
            
            msg = TurboBeeMsg(target='2019MNRAS.482.1872B')
            tasks.task_harvest_bumblebee(msg)
            self.assertEquals(loader.call_args[0], ('https://ui.adsabs.harvard.edu/#abs/2019MNRAS.482.1872B/abstract',))
            self.assertEquals(msg.target, '//ui.adsabs.harvard.edu/abs/2019MNRAS.482.1872B/abstract')
            self.assertTrue(next_task.called)
            self.assertTrue(msg.updated.seconds > 0)
            self.assertTrue(msg.expires.seconds >= msg.updated.seconds + 24*60*60)
            self.assertTrue(msg.eol.seconds >= msg.updated.seconds + 24*60*60*30)
            self.assertTrue(msg.ctype == msg.ContentType.html)

            
            msg = TurboBeeMsg(target='https://dev.adsabs.harvard.edu/#abs/foobar')
            tasks.task_harvest_bumblebee(msg)
            self.assertEquals(loader.call_args[0], ('https://dev.adsabs.harvard.edu/#abs/foobar',))
            self.assertEquals(msg.target, '//dev.adsabs.harvard.edu/abs/foobar')
            
            
            msg = TurboBeeMsg(target='https://dev.adsabs.harvard.edu/abs/foobar')
            tasks.task_harvest_bumblebee(msg)
            self.assertEquals(loader.call_args[0], ('https://dev.adsabs.harvard.edu/#abs/foobar',))
            self.assertEquals(msg.target, '//dev.adsabs.harvard.edu/abs/foobar')
            
            msg = TurboBeeMsg(target='//dev.adsabs.harvard.edu/abs/foobar')
            tasks.task_harvest_bumblebee(msg)
            self.assertEquals(loader.call_args[0], ('https://dev.adsabs.harvard.edu/#abs/foobar',))
            self.assertEquals(msg.target, '//dev.adsabs.harvard.edu/abs/foobar')
            
            

if __name__ == '__main__':
    unittest.main()
