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
from requests.exceptions import ConnectionError

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


    def test_connection_error(self):
        
        msg = TurboBeeMsg(qid='foo', value='bar', target='http://www.google.com')
        self.app.conf['PUPPETEER_ENDPOINT'] = 'http://localhost:30012222/scrape'
        try:
            self.app.harvest_webpage(msg)
        except ConnectionError:
            pass


    def test_bumblebee_template(self):
        html = ''
        with open(os.path.dirname(__file__) + '/abs.html', 'r') as f:
            html = f.read()
            
        with patch.object(self.app, '_load_url', return_value=html) as loader:
            tmpl = self.app.get_bbb_template('https://ui.adsabs.harvard.edu/#abs/2019LRR....22....1I/abstract')
            assert tmpl == self.app._tmpls['ui.adsabs.harvard.edu:abs']
            assert loader.called
            assert '{{tags}}' in tmpl
            assert '{{abstract}}' in tmpl
            assert '{{bibcode}}' in tmpl
            assert '__PRERENDERED' in tmpl
            
            assert '{{tags}}' not in html
            assert '{{abstract}}' not in html
            assert '{{bibcode}}' not in html
            assert loader.call_count == 1
            
            
            tmpl = self.app.get_bbb_template('https://ui.adsabs.harvard.edu/#abs/2019LRR....22....1I/abstract')
            assert loader.call_count == 1


    def test_build_abstract_page(self):
        msg = TurboBeeMsg(target='https://ui.adsabs.harvard.edu/#abs/2019LRR....22....1I/abstract')
        
        html = ''
        with open(os.path.dirname(__file__) + '/abs.html', 'r') as f:
            html = f.read()
        
        json = {u'responseHeader': {u'status': 0, u'QTime': 12, u'params': {u'x-amzn-trace-id': u'Root=1-5c89826f-96274e0a2ef0646da1cdc944', u'rows': u'10', u'q': u'identifier:"2019LRR....22....1I"', u'start': u'0', u'wt': u'json', u'fl': u'[citations],abstract,aff,author,bibcode,citation_count,comment,data,doi,esources,first_author,id,isbn,issn,issue,keyword,links_data,page,property,pub,pub_raw,pubdate,pubnote,read_count,title,volume,year'}}, u'response': {u'start': 0, u'numFound': 1, u'docs': [{u'read_count': 514, u'pubdate': u'2019-12-00', u'first_author': u'Ishak, Mustapha', u'abstract': u'We review recent developments and results in testing general relativity (GR) at cosmological scales. The subject has witnessed rapid growth during the last two decades with the aim of addressing the question of cosmic acceleration and the dark energy associated with it. However, with the advent of precision cosmology, it has also become a well-motivated endeavor by itself to test gravitational physics at cosmic scales. We overview cosmological probes of gravity, formalisms and parameterizations for testing deviations from GR at cosmological scales, selected modified gravity (MG) theories, gravitational screening mechanisms, and computer codes developed for these tests. We then provide summaries of recent cosmological constraints on MG parameters and selected MG models. We supplement these cosmological constraints with a summary of implications from the recent binary neutron star merger event. Next, we summarize some results on MG parameter forecasts with and without astrophysical systematics that will dominate the uncertainties. The review aims at providing an overall picture of the subject and an entry point to students and researchers interested in joining the field. It can also serve as a quick reference to recent results and constraints on testing gravity at cosmological scales.', u'links_data': [u'{"access": "open", "instances": "", "title": "", "type": "preprint", "url": "http://arxiv.org/abs/1806.10122"}', u'{"access": "open", "instances": "", "title": "", "type": "electr", "url": "https://doi.org/10.1007%2Fs41114-018-0017-4"}'], u'year': u'2019', u'pubnote': [u'Invited review article for Living Reviews in Relativity. 201 pages, 17 figures. Matches published version; doi:10.1007/s41114-018-0017-4'], u'id': u'15558883', u'bibcode': u'2019LRR....22....1I', u'author': [u'Ishak, Mustapha'], u'aff': [u'Department of Physics, The University of Texas at Dallas, Richardson, TX, USA'], u'esources': [u'EPRINT_HTML', u'EPRINT_PDF', u'PUB_HTML'], u'issue': u'1', u'pub_raw': u'Living Reviews in Relativity, Volume 22, Issue 1, article id. 1, <NUMPAGES>204</NUMPAGES> pp.', u'pub': u'Living Reviews in Relativity', u'volume': u'22', u'doi': [u'10.1007/s41114-018-0017-4'], u'keyword': [u'Tests of relativistic gravity', u'Theories of gravity', u'Modified gravity', u'Cosmological tests', u'Post-Friedmann limit', u'Gravitational waves', u'Astrophysics - Cosmology and Nongalactic Astrophysics', u'Astrophysics - Astrophysics of Galaxies', u'General Relativity and Quantum Cosmology'], u'title': [u'Testing general relativity in cosmology'], u'citation_count': 18, u'[citations]': {u'num_citations': 18, u'num_references': 928}, u'property': [u'ESOURCE', u'ARTICLE', u'REFEREED', u'PUB_OPENACCESS', u'EPRINT_OPENACCESS', u'EPRINT_OPENACCESS', u'OPENACCESS'], u'page': [u'1']}]}}

        with patch.object(self.app, '_load_url', return_value=html) as loader, \
            patch.object(self.app, 'search_api', return_value=json) as searcher:
            assert self.app.build_static_page(msg)
            p = msg.get_value().decode('utf8')
            assert u'og:image' in p
            assert u'We review recent' in p


    
if __name__ == '__main__':
    unittest.main()
