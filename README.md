[![Build Status](https://travis-ci.org/adsabs/ADSTurboBeePipeline.svg?branch=master)](https://travis-ci.org/adsabs/ADSTurboBeePipeline)
[![Coverage Status](https://coveralls.io/repos/github/adsabs/ADSTurboBeePipeline/badge.svg)](https://coveralls.io/github/adsabs/ADSTurboBeePipeline)

# ADSTurboBee

Pipeline (set of workers) for populating TurboBee (store).

       

## Short Summary



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

