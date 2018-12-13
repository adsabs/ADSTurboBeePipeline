
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
exch = Exchange(app.conf.get('CELERY_DEFAULT_EXCHANGE', 'turbobee'), 
                type=app.conf.get('CELERY_DEFAULT_EXCHANGE_TYPE', 'topic'))
app.conf.CELERY_QUEUES = (
    Queue('errors', exch, routing_key='errors', durable=False, message_ttl=24*3600*5),
    Queue('bumblebee', exch, routing_key='bumblebee'),
    Queue('user', exch, routing_key='user'),
)


logger = adsputils.setup_logging('adstb', app.conf.get('LOGGING_LEVEL', 'INFO'))


# connection to the other virtual host (for sending data out)
forwarding_connection = BrokerConnection(app.conf.get('OUTPUT_CELERY_BROKER',
                              '%s/%s' % (app.conf.get('CELRY_BROKER', 'pyamqp://'),
                                         app.conf.get('OUTPUT_EXCHANGE', 'master-pipeline'))))
class MyTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('{0!r} failed: {1!r}'.format(task_id, exc))



# ============================= TASKS ============================================= #

@app.task(base=MyTask, queue='bumblebee')
def task_bumblebee(message):
    """
    Typically, messages that we fetch from the queue gives us
    signals to update/create static view of bumblebee pages.
    

    :param: message: protocol buffer of type TurboBeeMsg
    :return: no return
    """
    
    if message.url:
        app.harvest_webpage(message.url)        
        
    
    

if __name__ == '__main__':
    app.start()