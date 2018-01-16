# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import os
import sys
import random
import urllib2
import logging
import numpy as np
from threading import Thread, Lock
from Queue import Queue

#import zhdfs
from zedge_common import *
from zedge_convnet import ZedgeConvNet
from zedge_dict_check import DictionaryCheck
from zedge_utils import resize

task_queue = Queue()   # thread-safe queue for tasks
#zfs = zhdfs.connect(HADOOP_HOST, HADOOP_PORT)
zfs = None
#zfp = zcv.init_cv_face_detector('/usr/share/OpenCV/haarcascades')
dict_check = DictionaryCheck()


#def copy_to_local_fast(filepath, temppath):
#    global zfs
#    zhdfs.get(zfs, filepath, temppath)

#def copy_to_local_fast_timeout(filepath, temppath):
#    global zfs
#    finished = False
#    for timeout in CONN_TIMEOUT_INTERVALS:
#        try:
#            zhdfs.get_timeout(zfs, filepath, temppath, timeout)
#            finished = True
#            break
#        except IOError, e:
#            print(str(e))
#            print('disconnecting...')
#            zhdfs.disconnect(zfs)
#            zfs = zhdfs.connect(HADOOP_HOST, HADOOP_PORT)
#            print('reconnected.')
#
#    if not finished:
#        raise IOError('could not copy %s to %s' % (filepath, temppath))

#def copy_to_local(filepath, temppath):
#   copy_to_local_fast(filepath, temppath)
#    copy_to_local_fast_timeout(filepath, temppath)

def get_temp_path(filename):
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    return os.path.join(TEMP_FOLDER, os.path.basename(filename))


class Item(object):
    def __init__(self, **kwargs):
        self.common_fields = {field: kwargs.get(field) for field in COMMON_FIELDS}
        self.result = {}
        self.lock = Lock()

    def __str__(self):
        return str(self.__dict__)

    def key(self):
        pass

    def get_result(self):
        try:
            self.lock.acquire()
            return self.result
        finally:
            self.lock.release()

    def update_result(self, field, decision):
        try:
            self.lock.acquire()
            self.result[field] = (self.result.get(field, False) or decision)
        finally:
            self.lock.release()

    def update_status(self, status):
        try:
            self.lock.acquire()
            if STATUS in self.result:
                if self.result[STATUS] == SUCCESS:
                    self.result[STATUS] = status
            else:
                self.result[STATUS] = status
        finally:
            self.lock.release()

    def update_txt_field(self, field, txt):
        try:
            self.lock.acquire()
            if field in self.result and len(self.result[field]) != 0:
                self.result[field] = self.result[field] + ';' + txt
            else:
                self.result[field] = txt
        finally:
            self.lock.release()

    def update_status_txt(self, txt):
        self.update_txt_field(STATUS_TXT, txt)

    def classify_text(self):
        global dict_check
        decision, txt = dict_check.is_family_unfriendly(self.common_fields)
        self.update_status(SUCCESS)
        self.update_status_txt(txt)
        self.update_result(TEXT_EXPLICIT_FIELD, decision)


class ItemText(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.lookup_id = kwargs.get('lookup_id')

    def key(self):
        return self.lookup_id


class ItemImage(Item):
    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.lookup_id = kwargs.get('lookup_id', None)
        self.remote_path = kwargs.get('filename')
        self.local_path = None

    def key(self):
        return self.remote_path if self.lookup_id is None else self.lookup_id

    def copy_to_local(self):
        logging.debug('started copy_to_local %s' % (self.remote_path))
        temp_path = get_temp_path(self.remote_path)
        if self.remote_path.startswith('http://'):
            self.local_path, res, err = self.copy_to_local_from_http(temp_path)
        else:
            #self.local_path, res, err = self.copy_to_local_from_hdfs(temp_path)
            res = False
            err = "HDFS not supported"
        if not res:
            self.local_path = None
            self.update_status(FAILURE)
            self.update_status_txt(err)
        logging.debug('finished copy_to_local %s' % (self.remote_path))
        return res

    def copy_to_local_from_http(self, temp_path):
        try:
            remote = urllib2.urlopen(self.remote_path, timeout=HTTP_TIMEOUT)
            local = open(temp_path, 'wb')
            local.write(remote.read())
            local.close()
            if USE_PY: resize(temp_path)
            return temp_path, True, ''
        except Exception, e:
            return None, False, str(e)

#    def copy_to_local_from_hdfs(self, temp_path):
#        try:
#            if os.path.exists(temp_path):
#                os.remove(temp_path)
#            copy_to_local(self.remote_path, temp_path)
#            if USE_PY: resize(temp_path)
#            return temp_path, True, ''
#        except IOError, e:
#            return None, False, str(e)

    def get_local_path(self):
        return self.local_path

    def remove_temp_file(self):
        try:
            os.remove(self.local_path)
            os.remove(get_crc_filename(self.local_path))
        except:
            pass


class Task(object):
    def __init__(self, req, wait_cond):
        self.image_items, self.text_items = Task.parse(req)
        self.wait_cond = wait_cond
        self.completed = False

    @staticmethod
    def parse(req):
        images = []
        texts = []
        for tp, it in req.items():
            if tp == WALLPAPERS_FIELD:
                images.extend([ItemImage(**z) for z in it])
            else:
                texts.extend([ItemText(**z) for z in it])
        return (images, texts)

    def mark_completed(self):
        self.wait_cond.acquire()
        self.completed = True
        self.wait_cond.notify()
        self.wait_cond.release()

    def is_completed(self):
        return self.completed

    def __str__(self):
        buf = []
        buf.extend([str(z) for z in self.image_items])
        buf.extend([str(z) for z in self.text_items])
        return '\n'.join(buf)

    def classify(self, image_classifiers):
        self.classify_image(image_classifiers)
        self.classify_text()

    def classify_text(self):
        logging.debug('classify_image %s' % (self))
        [item.classify_text() for item in self.text_items]

    def classify_image(self, image_classifiers):
        logging.debug('classify_image %s' % (self))
        [item.classify_text() for item in self.image_items]
        copied_items = self.copy_to_local()
        if len(copied_items) != 0:
            self.classify_convnet(copied_items, image_classifiers)
            #self.classify_cv_face(copied_items)
            [item.remove_temp_file() for item in copied_items]

    def copy_to_local(self):
        return [item for item in self.image_items if item.copy_to_local()]

    def classify_convnet(self, copied_items, image_classifiers):
        try:
            #def predict(c, items):
            #    try:
            #        ret = c.predict([item.get_local_path() for item in items])
            #        self.update_batch_result(items, ret, c.decision_field(), c.output_field())
            #    except Exception, e:
            #        logging.exception(e)
            #        self.update_batch_status(items, FAILURE, str(e))
            #threads = []
            #for c in image_classifiers:
            #    threads.append(Thread(target=predict, args=(c, copied_items)))
            #for t in threads:
            #    t.start()
            #for t in threads:
            #    t.join()
            for c in image_classifiers:
                res = c.predict([item.get_local_path() for item in copied_items])
                self.update_batch_result(copied_items, res, c.decision_field(), c.output_field())
        except Exception, e:
            logging.exception(e)
            self.update_batch_status(copied_items, FAILURE, str(e))

    #def classify_cv_face(self, copied_items):
    #    global zfp
    #    try:
    #        cv_face = {}
    #        for item in copied_items:
    #            face_found = zcv.detect_face(zfp, item.get_local_path())
    #            cv_face[item.get_local_path()] = {
    #                FACE: face_found,
    #                FACE_OUTPUT: '[cv_face,' + str(face_found) + ']'
    #            }
    #        self.update_batch_result(copied_items, cv_face, FACE, FACE_OUTPUT)
    #    except Exception, e:
    #        logging.exception(e)

    def update_batch_result(self, copied_items, conv_result, decision_field, output_field):
        inv = {}
        vis = {}
        for item in copied_items:
            inv[item.get_local_path()] = item
            vis[item] = False

        for local_path, result in conv_result.items():
            if local_path in inv:
                item = inv[local_path]
                item.update_result(decision_field, result[decision_field])
                item.update_txt_field(output_field, result[output_field])
                vis[item] = True
            else:
                logging.error('>>> %s is not in %s' % (local_path, inv))

        for item, v in vis.items():
            if not v:
                logging.error('>>> item %s is not checked' % (item))

    def update_batch_status(self, copied_items, status, status_txt):
        for item in copied_items:
            item.update_status(status)
            item.update_status_txt(status_txt)

    def get_result(self):
        result = {}
        for items in [self.text_items, self.image_items]:
            for item in items:
                result[item.key()] = item.get_result()
        return result


class Worker(Thread):
    def __init__(self):
        Thread.__init__(self)
        print IMAGE_CLASSIFIERS
        self.image_classifiers = [ZedgeConvNet(c) for c in IMAGE_CLASSIFIERS]

    def run(self):
        global task_queue
        while True:
            task = task_queue.get()
            logging.debug('got a task %s' % (task))
            task.classify(self.image_classifiers)
            try:
                task_queue.task_done()
            except ValueError, e:
                logging.debug(str(e))
            task.mark_completed()
