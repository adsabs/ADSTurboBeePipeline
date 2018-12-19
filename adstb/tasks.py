
from __future__ import absolute_import, unicode_literals
from adstb import app as app_module
import adsputils
from adstb import exceptions
from adstb.models import KeyValue
from celery import Task
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue, BrokerConnection
import datetime


# ============================= INITIALIZATION ==================================== #

app = app_module.create_app()
exch = Exchange(app.conf.get('CELERY_DEFAULT_EXCHANGE', 'turbobee_pipeline'), 
                type=app.conf.get('CELERY_DEFAULT_EXCHANGE_TYPE', 'topic'))
app.conf.CELERY_QUEUES = (
    Queue('harvest-bumblebee', exch, routing_key='bumblebee'),
    Queue('output-results', exch, routing_key='output'),
)




# ============================= TASKS ============================================= #

@app.task(queue='harvest-bumblebee')
def task_harvest_bumblebee(message):
    """
    Typically, messages that we fetch from the queue gives us
    signals to update/create static view of bumblebee pages.
    

    :param: message: protocol buffer of type TurboBeeMsg
    :return: no return
    """
    
    if message.target:
        v = app.harvest_webpage(message)
        if v:
            task_output_results.delay(message)
        
        
    
@app.task(queue='output-results', retry_limit=2)
def task_output_results(message):
    """Receives the messages from the workers and updates
    the store (remote microservice)
    
    :param: message: protocol buffer of type TurboBeeMsg
    :return: no return
    """
    
    qid = app.update_store(message)
    app.logger.debug('Delivered: qid=%s, target=%s', qid, message.target)
    
    

if __name__ == '__main__':
    app.start()