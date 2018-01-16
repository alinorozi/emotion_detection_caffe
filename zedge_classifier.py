# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import sys
import os
import json
import logging
import logging.config
import logging.handlers
from threading import Condition
from threading import Thread
from functools import wraps
from time import time
import numpy as np

import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen

sys.path.insert(0, os.path.abspath('caffe/python'))
#sys.path.insert(0, os.path.abspath('caffe-gil/distribute/python'))
import caffe

from zedge_common import HADOOP_HOST, HADOOP_PORT, TORNADO_PORT, NUM_WORKERS, CPU_MODE
from zedge_worker import task_queue, zfs, Task, Worker

def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        f = Thread(target=func, args=args, kwargs=kwargs)
        f.start()
        return f
    return wrapper

@run_async
def handle_post(req, callback):
    try:
        started = time()
        logging.info('req %s' % (req))
        wait_cond = Condition()
        new_task = Task(req, wait_cond)
        logging.debug('adding new task to queue')
        logging.debug(new_task)
        task_queue.put(new_task)
        logging.debug('waiting for completion of task')
        wait_cond.acquire()
        while not new_task.is_completed(): wait_cond.wait()
        wait_cond.release()
        result = json.dumps(new_task.get_result())
        logging.info('request: ' + json.dumps(req) + ' response: ' + str(result))
        elapsed = time() - started
        logging.debug('req %s completed after %f secs' % (req, elapsed))
        callback({'status': 200, 'result': result})
    except Exception, e:
        logging.exception(e)
        callback({'status': 500, 'result': str(e)})

class ClassifierHandler(tornado.web.RequestHandler):
    def get(self):
        logging.info('OK')
        self.write('OK')
        self.finish()

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        req = tornado.escape.json_decode(self.request.body)
        response = yield tornado.gen.Task(handle_post, req)
        self.clear()
        self.set_status(response['status'])
        self.write(response['result'])
        self.finish()

if __name__ == "__main__":
    logging.config.fileConfig('zedge_log.cfg')

    if CPU_MODE == 0:
        caffe.set_mode_gpu()
        logging.info('set GPU mode for caffe')
    else:
        caffe.set_mode_cpu()
        logging.info('set CPU mode for caffe')

    logging.info('creating %d workers' % (NUM_WORKERS))
    for _ in range(NUM_WORKERS):
        worker = Worker()
        worker.daemon = True
        worker.start()

    application = tornado.web.Application([
        (r"/classifier", ClassifierHandler),
    ])

    logging.info('classifier is running on port %d' % (TORNADO_PORT))
    application.listen(TORNADO_PORT)
    tornado.ioloop.IOLoop.instance().start()

    if zfs is not None:
        zhdfs.disconnect(zfs)
