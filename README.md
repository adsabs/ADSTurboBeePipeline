[![Build Status](https://travis-ci.org/adsabs/ADSTurboBeePipeline.svg?branch=master)](https://travis-ci.org/adsabs/ADSTurboBeePipeline)
[![Coverage Status](https://coveralls.io/repos/github/adsabs/ADSTurboBeePipeline/badge.svg)](https://coveralls.io/github/adsabs/ADSTurboBeePipeline)

# ADSTurboBee

Pipeline (set of workers) for populating TurboBee (store).

       

## Short Summary
Create and cache static html abstract pages that hydrate to a bumblebee page.  This is useful for crawlers and faster page loading.
The cache page is built using a template and the results from a single request to /v1/search/query.  The abstract page template is computed by a chromiumn browser running in a separate process.  This browser downloads the bumblebee abstract page.  The cached page is persisted using a post to /v1/store/update which is handled by the turbobee service.

To process a single bibcode, one could:
```root@linuxkit-025000000001:/app# python run.py -q '{"q": "bibcode:2003ASPC..295..361M"}'```

And this is essentially what happens if you use the --filename option to provide a list of bibcodes.

One can test the scraper in the turbobee pipeline container with:
```root@linuxkit-025000000001:/app# curl 'localhost:3001/scrape' -X POST -d '["https://dev.adsabs.harvard.edu/#abs/2019LRR....22....1I/abstract"]' -H 'Content-Type: application/```



## Queues and objects

    - bumblebee
        Messages that go into the queue are consumed by workers that update static pages
    - user
        Messages from this queue are consumed by workers that update user specific content (it is exactly parallel to bumblebee, but deals with different content; api requests etc). 



## Setup (recommended)

    `$ cd adstb/`
    `$ virtualenv python`
    `$ source python/bin/activate`
    `$ pip install -r requirements.txt`
    `$ pip install -r dev-requirements.txt`
    `$ vim local_config.py` # edit, edit
    `$ alembic upgrade head` # initialize database
    
## Testing

Always write unittests (even: always write unitests first!). Travis will run automatically. On your desktop run:

    `$ py.test`
    

## Maintainer(s)

Roman

