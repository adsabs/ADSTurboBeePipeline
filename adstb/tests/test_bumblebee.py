#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os

import unittest
from adstb.models import KeyValue
from adstb.models import Base
from adstb import bumblebee
from adsmsg import TurboBeeMsg
from mock import patch, MagicMock
from requests.exceptions import ConnectionError

class TestBumblebee(unittest.TestCase):
    response = {u'response': {u'docs': [{u'[citations]': {u'num_citations': 18,
         u'num_references': 928},
        u'abstract': u'We review recent developments and results in testing general relativity (GR) at cosmological scales. The subject has witnessed rapid growth during the last two decades with the aim of addressing the question of cosmic acceleration and the dark energy associated with it. However, with the advent of precision cosmology, it has also become a well-motivated endeavor by itself to test gravitational physics at cosmic scales. We overview cosmological probes of gravity, formalisms and parameterizations for testing deviations from GR at cosmological scales, selected modified gravity (MG) theories, gravitational screening mechanisms, and computer codes developed for these tests. We then provide summaries of recent cosmological constraints on MG parameters and selected MG models. We supplement these cosmological constraints with a summary of implications from the recent binary neutron star merger event. Next, we summarize some results on MG parameter forecasts with and without astrophysical systematics that will dominate the uncertainties. The review aims at providing an overall picture of the subject and an entry point to students and researchers interested in joining the field. It can also serve as a quick reference to recent results and constraints on testing gravity at cosmological scales.',
        u'aff': [u'Department of Physics, The University of Texas at Dallas, Richardson, TX, USA'],
        u'author': [u'Ishak, Mustapha'],
        u'bibcode': u'2019LRR....22....1I',
        u'doi': [u'10.1007/s41114-018-0017-4'],
        u'esources': [u'EPRINT_HTML', u'EPRINT_PDF', u'PUB_HTML'],
        u'first_author': u'Ishak, Mustapha',
        u'issue': u'1',
        u'identifier': ["2011arXiv1108.0669H", "2012ApJS..199...26H", "arXiv:1108.0669", "10.1088/0067-0049/199/2/26"],
        u'keyword': [u'Tests of relativistic gravity',
         u'Theories of gravity',
         u'Modified gravity',
         u'Cosmological tests',
         u'Post-Friedmann limit',
         u'Gravitational waves',
         u'Astrophysics - Cosmology and Nongalactic Astrophysics',
         u'Astrophysics - Astrophysics of Galaxies',
         u'General Relativity and Quantum Cosmology'],
        u'links_data': [u'{"access": "open", "instances": "", "title": "", "type": "preprint", "url": "http://arxiv.org/abs/1806.10122"}',
         u'{"access": "open", "instances": "", "title": "", "type": "electr", "url": "https://doi.org/10.1007%2Fs41114-018-0017-4"}'],
        u'page': [u'1'],
        u'page_range': u'41-59',
        u'property': [u'ESOURCE',
         u'ARTICLE',
         u'REFEREED',
         u'PUB_OPENACCESS',
         u'EPRINT_OPENACCESS',
         u'EPRINT_OPENACCESS',
         u'OPENACCESS'],
        u'pub': u'Living Reviews in Relativity',
        u'pubdate': u'2019-12-00',
        u'title': [u'Testing general relativity in cosmology'],
        u'volume': u'22',
        u'year': u'2019'}],
      u'numFound': 1,
      u'start': 0},
     u'responseHeader': {u'QTime': 1,
      u'params': {u'fl': u'links_data,[citations],keyword,property,first_author,year,issn,isbn,title,aff,abstract,bibcode,pub,volume,author,issue,pubdate,doi,page,esources,data',
       u'q': u'bibcode:2019LRR....22....1I',
       u'rows': u'10',
       u'start': u'0',
       u'wt': u'json',
       u'x-amzn-trace-id': u'Root=1-5c868f1d-3d3ee86785ee9c172fdca34c'},
      u'status': 0}}

    x = bumblebee.build_meta_tags(response['response']['docs'][0])
    assert '<meta name="citation_doi" content="10.1007/s41114-018-0017-4" data-highwire="true">' in x
    assert '<meta name="og:description" content="We review recent' in x
    assert '<meta name="citation_lastpage" content="59"' in x
    assert '<meta name="prism.endingPage" content="59"' in x
    assert '<meta name="citation_arxiv_id" content="arXiv:1108.0669"' in x
    
    x = bumblebee.build_abstract(response['response']['docs'][0])
    assert 'Gravitational waves;' in x
    assert '<dt>DOI:</dt>' in x
    assert '<dd>December 2019</dd>' in x
    assert 'We review recent developments' in x
    assert 'Texas at Dallas, Richardson' in x
    assert 'Ishak, Mustapha' in x

    x = bumblebee._html_to_text(u'Renormalization of quark propagators from twisted-mass lattice QCD at N<SUB>f</SUB>=2')
    assert x == u'Renormalization of quark propagators from twisted-mass lattice QCD at Nf=2'
    x = bumblebee._html_to_text(u'Renormalization of quark propagators from twisted-mass lattice QCD at N&lt;SUB&gt;f&lt;/SUB&gt;=2')
    assert x == u'Renormalization of quark propagators from twisted-mass lattice QCD at Nf=2'
    
if __name__ == '__main__':
    unittest.main()    
