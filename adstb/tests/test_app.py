#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os

import unittest
from adstb.models import KeyValue
import testing.postgresql
from adstb.models import Base
from adstb import app
from adsmsg import TurboBeeMsg
from mock import patch, MagicMock

class TestTurboBeeCelery(unittest.TestCase):
    """
    Tests the appliction's methods
    """
    
    @classmethod
    def setUpClass(cls):
        cls.postgresql = \
            testing.postgresql.Postgresql(host='127.0.0.1', port=15678, user='postgres', 
                                          database='test')

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()
        

    def setUp(self):
        unittest.TestCase.setUp(self)
        
        proj_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        self.app = app.ADSTurboBeeCelery('test', local_config=\
            {
            'SQLALCHEMY_URL': 'sqlite:///',
            'SQLALCHEMY_ECHO': False,
            'PROJ_HOME' : proj_home,
            'TEST_DIR' : os.path.join(proj_home, 'adstb/tests'),
            'UPDATE_ENDPOINT': 'https://api.adsabs.harvard.edu/v1/store/update'
            })
        Base.metadata.bind = self.app._session.get_bind()
        Base.metadata.create_all()
        

    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        Base.metadata.drop_all()
        self.app.close_app()

    
    def test_app(self):
        assert self.app._config.get('SQLALCHEMY_URL') == 'sqlite:///'
        assert self.app.conf.get('SQLALCHEMY_URL') == 'sqlite:///'

    
    def test_update_store(self):
        msg = TurboBeeMsg(qid='foo', value='bar')
        msg2 = TurboBeeMsg(qid='foo', value='bar')
        resp = MagicMock()
        resp.raise_for_status = lambda : 1
        with patch.object(self.app._client, 'post', return_value=resp) as post:
            r = self.app.update_store([msg, msg2])
            
            assert post.call_args[0][0] == u'https://api.adsabs.harvard.edu/v1/store/update'
            assert len(post.call_args[1]['files']) == 2
            assert post.call_args[1]['files']['0'] == '\n\x03fooR\x03bar'

    
if __name__ == '__main__':
    unittest.main()
