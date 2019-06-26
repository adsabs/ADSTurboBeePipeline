
# -*- coding: utf-8 -*-

from .models import KeyValue
import adsputils
from adsputils import get_date, setup_logging, load_config, ADSCelery, u2asc, ADSTask
from adstb.exceptions import InvalidContent
from adstb import bumblebee
from adsmsg import TurboBeeMsg
import time
from requests.exceptions import ConnectionError
import traceback
from urlparse import urlparse

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


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
        self._tmpls = {}
    
    def _pick_bbb_url(self, url):
        """This method will return a hash version of an url;
        and the push-state version of the URL; we'll always
        save the push-state because that is what the webserver
        can see."""
        
        scheme = ''
        if '://' in url:
            scheme, url = url.split('://')
            scheme += '://'
        elif url.startswith('//'):
            scheme, url = 'https://', url.replace('//', '', 1)
        
        if '#' in url:
            for x in bbb_paths:
                k = '#' + x + '/'
                if k in url:
                    return scheme + url, '//' + url.replace(k, x + '/')
        else:
            for x in bbb_paths:
                k = x + '/'
                if k in url:
                    return scheme + url.replace(k, '#' + x + '/'), '//' + url  
            
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
        
        
        hash_url, pushstate_url = self._pick_bbb_url(url)
        self.logger.info('Going to harvest: %s (and save as: %s)', hash_url, pushstate_url)
        html = self._load_url(hash_url)
        message.target = pushstate_url
        message.set_value(html, message.ContentType.html)
        self._update_timestamps(message)
        return True

    def _update_timestamps(self, message):
        # update tiemstamps
        message.updated = message.get_timestamp()
        message.expires.seconds = message.updated.seconds + self.conf.get('BBB_EXPIRATION_SECS', 60*60*24) # 24h later
        message.eol.seconds = message.updated.seconds + self.conf.get('BBB_EOL_SECS', 60*60*24*90) # 3 months later
        
        if not message.created.seconds:
            message.created = message.updated

    def _load_url(self, url):
        try:
            self.logger.debug('trying to load url {} at endpoint: {}'.format(url, self.conf.get('PUPPETEER_ENDPOINT')))
            r = requests.post(self.conf.get('PUPPETEER_ENDPOINT', 'http://localhost:3001/scrape'),
                json=[url])
            r.raise_for_status()
            self.logger.debug('success loaded page at {} with encoding {} and {}'.format(url, r.encoding, r))
            self._err_counter = 0
            j = r.json()
            return j[url]
        except Exception as e:
            self._err_counter += 1
            self.logger.error('_load_url original error {}'.format(traceback.format_exc()))
            self.logger.error('_load_url failed for url {} with {}'.format(url, str(e)))
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
        b = urlparse(url)
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
            return None  # can't find it
        
    def update_store(self, message):
        """Delivers the message to the remote api side.
        
        :param: message - protobuf of TurboBeeMsg
        :return: qid - qid when operation succeeded
        """
        self.logger.info('updating store with {}'.format(str(message)[:30]))
        r = self._post(self.conf.get('UPDATE_ENDPOINT'), message)
        r.raise_for_status()
        return r

    def iscachable(target):
        """Returns True if the passed target should be processed """
        if target.endswith('.ico'):
            # we don't cache icons
            return False
        if '/doi:' in target:
            # abstract urls with a doi are not currently supported by bumblebee
            return False
        return True

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
            self.logger.warn('Cannot establish connection with the crawler; blocking for %s seconds', 2**self._err_counter )
            time.sleep(2**self._err_counter)
    
    def build_static_page(self, message):
        """Will assemble BBBB abstract page using a template
        and a data from the API."""
        
        if not message.target:
            return None
        
        url = message.target
        parts = self._parse_bbb_url(url)
        hash_url, pushstate_url = self._pick_bbb_url(url)
        self.logger.info('Going to assemble: %s (and save as: %s)', hash_url, pushstate_url)
        
        if parts['pagename'] == 'abs':
            bibcode = parts.get('bibcode', None)
            if bibcode is None:
                raise Exception('Cannot identify bibcode in %s' % url)
            
            # list of fields used by components that we care about
            fl = '[citations],abstract,aff,author,bibcode,citation_count,comment,data,doi,esources,first_author,id,identifier,isbn,issn,issue,keyword,links_data,page,page_range,property,pub,pub_raw,pubdate,pubnote,read_count,title,volume,year'
            
            # on api failure error will be thrown and that triggers celery re-try
            solr_response = self.search_api(q='identifier:"%s"' % bibcode, fl=fl)
            abstract_tmpl = self.get_bbb_template(hash_url)
            
            if solr_response['response']['numFound'] == 0:
                self.logger.error('API found no doc with identifier:' + bibcode)
                return None
            elif solr_response['response']['numFound'] > 1:
                self.logger.warn('API found too many docs for query identifier: %s; we are taking the first one' % bibcode)
                
            data = solr_response['response']['docs'][0]
            tags = bumblebee.build_meta_tags(data, self.conf)
            abstract = bumblebee.build_abstract(data, max_authors=self.conf.get('BBB_ABSTRACT_MAX_AUTHORS', 8), 
                                              gateway_url=self.conf.get('BBB_ABSTRACT_GATEWAY_URL', '/link_gateway/'))
            
            html = abstract_tmpl.replace(u'{{tags}}', tags).replace(u'{{abstract}}', abstract)
            html = html.replace(u'{{bibcode}}', bibcode.strip())

            message.target = pushstate_url
            message.set_value(html, message.ContentType.html)
            self._update_timestamps(message)
            
            return True

    def search_api(self, **kwargs):
        r = self._client.get(self.conf.get('SEARCH_ENDPOINT'), params=kwargs)
        r.raise_for_status()
        return r.json()
        
    def _parse_bbb_url(self, url):
        """Parses url and extracts domain information as well as bbb
        pagename.
        """
        parts = urlparse(url)
        out = {'url': url}
        out['domain'] = parts.netloc
        # remove :80 port, if any
        if out['domain'].endswith(':80'):
            out['domain'] = out['domain'][0:-3]
            
        if parts.path == '/' and len(parts.fragment) > 1:
            out['pagename'] = parts.fragment.split('/')[0]
            out['bibcode'] = parts.fragment.split('/')[1]
        elif parts.path and len(parts.path) > 1:
            out['pagename'] = parts.path.split('/')[1]
            out['bibcode'] = parts.path.split('/')[2]
        else:
            out['pagename'] = 'unknown'
            out['bibcode'] = None
        return out 
        
    def get_bbb_template(self, target_url):
        """Finds the template that would work for a given url."""
        target_url = target_url.strip()
        parts = self._parse_bbb_url(target_url)
        
        pagename = parts['pagename']
        domain = parts['domain']
        
        if pagename == 'abs':
            if domain + ':' + pagename in self._tmpls:
                return self._tmpls[domain + ':' + pagename]
            tmpl = self._retrieve_abstract_template(target_url)
            if tmpl is None:
                raise Exception('Error harvesting page template for: ' + target_url)
            self._tmpls[domain + ':' + pagename] = tmpl
            return tmpl
        else:
            raise Exception('Unknown page type: %s' % pagename)

    def _retrieve_abstract_template(self, url):
        msg = TurboBeeMsg(target=url)
        i = 0

        parts = self._parse_bbb_url(url)
        
        while not self.harvest_webpage(msg) and i < 3:
            self.logger.warn('Retrying to fetch: ' + url)
            i += 1

        html = msg.get_value()
        html = html.decode('utf8')

        # some basic checks
        if 'data-widget="ShowAbstract"' not in html:            
            raise Exception('Cannot process fetched page, or data-widget for {}'.format(url))
        # TODO; find the sections and replace them with symbolic names {tags}, {abstract}....
        x = html.find('data-highwire')
        while x > 0:
            x -= 1
            if html[x] == '<':
                break
        end = html.find('data-highwire', x)
        while html.find('data-highwire', end+1) > 0:
            end = html.find('data-highwire', end+1)

        while html[end] != '>':
            end += 1
        if end == -1 or x == 0:
            raise Exception("Cannot find tags section")
        html = html[0:x] + '{{tags}}' + html[end+1:]

        
        x = html.find('<article')
        end = html.find('</article')
        
        if x == -1 or end == -1:
            raise Exception('Cannot process fetched page, cannot find abstract section for {}'.format(url))
        
        while x < len(html) and x < end:
            x += 1
            if html[x] == '>':
                x += 1
                break
            
        if x > end:
            raise Exception('Cannot process fetched page, cannot find abstract section for {}'.format(url))

        html = html[0:x] + '{{abstract}}' + html[end:]

        if 'bibcode' in parts and parts['bibcode']:
            html = html.replace(parts['bibcode'], u'{{bibcode}}')

        # finally, cut out noscript warning that says javascript is required
        x = html.find('id="noscriptmsg"')  # div id within noscript
        if x > -1:
            start = html.rfind('<noscript', 0, x)
            end = html.find('</noscript>', start) + len('</noscript>')
            if end > start:
                html = html[:start] + html[end:]
        # and the first noscript that includes a style, it hides the abstract div
        x = html.find('<noscript>')
        if x > -1:
            offset = x + len('<noscript>')
            if html[offset:].strip().startswith('<style>'):
                end = html.find('</noscript>') + len('</noscript>')
                if end > x:
                    html = html[:x] + html[end:]

        return html
        
        
