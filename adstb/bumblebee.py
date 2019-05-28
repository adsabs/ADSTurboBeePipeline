from pybars import Compiler
import copy
import urllib
from adsputils import get_date, parser
import re
import datetime


# this is from widgets/meta_tags/template
meta_tags_tmpl = u'''<meta name="og:type" content="article" data-highwire="true">
<meta name="twitter:card" content="summary" data-highwire="true">

<meta name="citation_title" content="{{title}}" data-highwire="true">
<meta name="og:title" content="{{title}}" data-highwire="true">
<meta name="twitter:title" content="{{title}}" data-highwire="true">

<meta name="og:url" content="{{url}}" data-highwire="true">
<meta name="twitter:url" content="{{url}}" data-highwire="true">
<meta name="citation_abstract_html_url" content="{{url}}" data-highwire="true">

<meta name="og:image" content="https://ui.adsabs.harvard.edu/styles/img/transparent_logo.svg" data-highwire="true">
<meta name="twitter:image" content="https://ui.adsabs.harvard.edu/styles/img/transparent_logo.svg" data-highwire="true">

{{#if abstract}}
<meta name="og:description" content="{{abstract}}" data-highwire="true">
<meta name="twitter:description" content="{{abstract}}" data-highwire="true">
{{/if}}
{{#each author}}
<meta name="citation_author" content="{{this.name}}" data-highwire="true">
<meta xmlns="http://www.w3.org/1999/xhtml" name="citation_author_institution" content="{{this.aff}}" data-highwire="true">
{{/each}}
{{#if page}}
<meta name="citation_firstpage" content="{{page}}" data-highwire="true">
{{/if}}
{{#if pubdate}}
<meta name="citation_publication_date" content="{{pubdate}}" data-highwire="true">
{{/if}}
{{#if pub}}
<meta name="citation_journal_title" content="{{pub}}" data-highwire="true">
{{/if}}
{{#if volume}}
<meta name="citation_volume" content="{{volume}}" data-highwire="true">
{{/if}}
{{#if issue}}
<meta name="citation_issue" content="{{issue}}" data-highwire="true">
{{/if}}
{{#if doi}}
<meta name="citation_doi" content="{{doi}}" data-highwire="true">
{{/if}}
{{#if issn}}
<meta name="citation_issn" content="{{issn}}" data-highwire="true">
{{/if}}
{{#each keyword}}
<meta name="citation_keywords" content="{{this}}" data-highwire="true">
{{/each}}
{{#if pdfUrl}}
<meta name="citation_pdf_url" content="{{pdfUrl}}" data-highwire="true">
{{/if}}
<script>window.__PRERENDERED = true;</script>'''



abstract_tmpl = u'''

<h2 class="s-abstract-title">
    {{{title}}}
    <a href="{{titleLink.href}}">{{titleLink.text}}</a>
</h2>




{{#if authorAff}}
{{#if hasAffiliation}}
<button class="btn btn-xs btn-default-flat s-toggle-aff" id="toggle-aff">Show affiliations</button>
{{/if}}
{{#if hasMoreAuthors}}
<button class="btn btn-xs btn-default-flat s-toggle-authors" id="toggle-more-authors">Show all authors</button>
{{/if}}

<div id="authors-and-aff" class="s-authors-and-aff">
    <ul class="list-inline">
        {{#each authorAff}}
        {{#if @last}}
        <li class="author"><a href="#search/q=author:{{href}}&sort=date%20desc,%20bibcode%20desc">{{name}}</a><span class="affiliation hide"> (<i>{{aff}}</i>)</span></li>
        {{else}}
        <li class="author"><a href="#search/q=author:{{href}}&sort=date%20desc,%20bibcode%20desc">{{name}}</a><span class="affiliation hide"> (<i>{{aff}}</i>)</span>;</li>
        {{/if}}
        {{/each}}
        {{#if hasMoreAuthors}}
        <li class="author extra-dots">; <a data-target="more-authors" title="Show all authors">...</a></li>
        {{/if}}
        {{#each authorAffExtra}}
        {{#if @last}}
        <li class="author extra hide"><a href="#search/q=author:{{href}}&sort=date%20desc,%20bibcode%20desc">{{name}}</a><span class="affiliation hide"> (<i>{{aff}}</i>)</span></li>
        {{else}}
        <li class="author extra hide"><a href="#search/q=author:{{href}}&sort=date%20desc,%20bibcode%20desc">{{name}}</a><span class="affiliation hide"> (<i>{{aff}}</i>)</span>;</li>
        {{/if}}
        {{/each}}
    </ul>
</div>
{{/if}}

<div class="s-abstract-text">
    <h4 class="sr-only">Abstract</h4>
    <p>
        {{#if abstract}}
        {{{abstract}}}
        {{else}}
        <i>No abstract</i>
        {{/if}}
    </p>
</div>

<br>
<dl class="s-abstract-dl-horizontal">

    {{#if pub_raw}}
    <dt>Publication</dt>
    <dd>
        <div id="article-publication">{{{pub_raw}}}</div>
    </dd>
    {{/if}}

    {{#if formattedDate}}
    <dt>Pub Date:</dt>
    <dd>{{formattedDate}}</dd>
    {{/if}}

    {{#if doi}}
    <dt>DOI:</dt>
    <dd>
        <span>
            <a href="{{doi.href}}" target="_blank" rel="noopener">{{doi.doi}}</a>
            <i class="fa fa-external-link"></i>
        </span>
    </dd>
    {{/if}}

    <dt>Bibcode</dt>
    <dd>{{bibcode}} <i class="icon-help" data-toggle="popover" data-content="The bibcode is assigned by the ADS as a unique identifier for the paper."></i></dd>

    {{#if keyword}}
    <div id="keywords">
        <dt>Keywords</dt>
        <dd>
            <ul class="list-inline">
                {{#each keyword}}
                {{#if @last}}
                <li>{{{this}}}</li>
                {{else}}
                <li>{{{this}}};</li>
                {{/if}}
                {{/each}}
            </ul>
        </dd>
    </div>
    {{/if}}

    {{#if comment}}
    <div id="comment">
        <dt>Comments</dt>
        <dd>
            <ul class="list-unstyled">
                {{#each commentList}}
                    <li>{{{this}}}</li>
                {{/each}}
                {{#if hasExtraComments}}
                    {{#if showAllComments}}
                    <li><a href="#" id="show-less-comments">show less</a></li>
                    {{else}}
                    <li><a href="#" id="show-all-comments">show all</a></li>
                    {{/if}}
                {{/if}}
            </ul>
        </dd>
    </div>
    {{/if}}


</dl>
<br/>
<a class="small pull-right text-faded" target="_blank" rel="noopener" href="http://adsabs.harvard.edu/adsfeedback/submit_abstract.php?bibcode={{bibcode}}" title="Provide feedback or suggest corrections">
    <span class="fa-stack">
        <i class="fa fa-comment-o fa-stack-2x"></i>
        <i class="fa fa-exclamation fa-stack-1x"></i>
    </span>
    Feedback/Corrections?
</a>

'''


compiler = Compiler()
meta_template = compiler.compile(meta_tags_tmpl)

acompiler = Compiler()
abstract_template = acompiler.compile(abstract_tmpl)

def build_meta_tags(solrdoc):
    """Builds meta tags section that is inserted into HTML of a page;
    it receives a solr document which must have at least those
    fields:
        'fl':'links_data,[citations],keyword,property,first_author,year,issn,isbn,title,aff,abstract,bibcode,pub,volume,author,issue,pubdate,doi,page,esources,data',
    """
    
    data = copy.deepcopy(solrdoc)

    if 'aff' in data:
        data['author'] = [{'name': x, 'aff': y} for x,y in zip(data['author'], data['aff'])]
    elif 'author' in data:
        data['author'] = [{'name': x, 'aff': '-'} for x in data['author']]
        
    if 'doi' in data:
        data['doi'] = data['doi'][0]
    return ''.join(meta_template(data))

def _format_date(d):
    i = 0
    f = [("%Y-%m-%d", "%B %d %Y"), ("%Y-%m", "%B %Y"), ("%Y", '%Y')]
    while d and i < 2:
        try:
            x = datetime.datetime.strptime(d, f[i][0])
            return x.strftime(f[i][1])
        except:
            d = d.replace('-00', '')
        finally:
            i += 1
    return d # default
            

def build_abstract(solrdoc, max_authors=20,
                   gateway_url='/link-gateway/'):
    """Equivalent to: https://github.com/adsabs/bumblebee/blob/d8830016fdc2bdf566363979b15b9ee57527f78e/src/js/widgets/abstract/widget.js#L53
    
    It modifies data from the API and then formats them using abstract template.
    """
    
    data = copy.deepcopy(solrdoc)
    bibcode = data['bibcode']
    
    
    if isinstance(data.get('doi', ''), list):
        data['doi'] = {'doi': data.get('doi'), 'href': gateway_url + bibcode + '/doi' + ':' + data['doi'][0]} 
    
    if 'author' in data or 'aff' in data:
        data['authorAff'] = [list(x) for x in zip(data['author'], data.get('aff', range(len(data['author']))))]
    data['hasAffiliation'] = len(filter(lambda x: x != '-', data.get('aff', []))) > 0
    
    if len(data.get('page', [])) > 1:
        data['page'] = data['page'][0]
                            
    
    if data.get('authorAff', None):
        for x in data['authorAff']: # add urls
            x.append('"' + urllib.quote(x[0].encode("utf-8")).replace('%20', "+") + '"')
        
        if len(data['authorAff']) > max_authors:
            data['authorAffExtra'] = data['authorAff'][max_authors:]
            data['authorAff'] = data['authorAff'][0:max_authors]
            data['hasMoreAuthors'] = True
        else:
            data['hasMoreAuthors'] = False
        data['authorAff'] = [{'name': x[0], 'aff': x[1], 'href': x[2]} for x in data['authorAff']]
    else:
        data['authorAff'] = []
    
    if 'hasMoreAuthors' not in data:
        data['hasMoreAuthors'] = False
    
    if data.get('pubdate', None):
        d = data['pubdate']
        data['formattedDate'] = _format_date(d)
        
    if isinstance(data.get('title', ''), list):
        data['title'] = data['title'][0]
        title = data['title']
        
        t_link = re.findall(r'<a[^>]*href="([^"]*?)".*?>([^\/]*)<\/a>', title, re.IGNORECASE);
        if t_link:
            data['titleLink'] = {'href': t_link[0][0], 'text': t_link[0][1]}
            if data['titleLink']['href'].startswith('/abs'):
                data['titleLink']['href'] = '#' + data['titleLink']['href'][1:]
                            
    if isinstance(data.get('comment', []), basestring):
        data['comment'] = data['comment'].split(';')
        
        
    if 'comment' in data:
        data['comment'] = data['comment'][0:3]
        
    
    return ''.join(abstract_template(data))
                
