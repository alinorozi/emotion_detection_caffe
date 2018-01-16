# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import os
import sys
import logging
import traceback
import numpy as np

#sys.path.insert(0, os.path.abspath('caffe/python'))
sys.path.insert(0, os.path.abspath('caffe-gil/distribute/python'))
import caffe

import zcaffe
from zedge_common import *
from zedge_utils import resize

class ZedgeConvNet(object):
    def __init__(self, cfg):
        logging.info('creating ZedgeConvNet:')
        [logging.info('    %s: %s' % (k, v)) for k, v in cfg.items()]
        self.cfg = cfg
        if USE_PY:
            self.classifier = caffe.Classifier(cfg['deploy_file_py'], cfg['trained_model'],
                image_dims=(256, 256), mean=np.load(cfg['mean_file']).mean(1).mean(1),
                raw_scale=255, channel_swap=(2,1,0))
        else:
            self.classifier = zcaffe.init_convnet(cfg['deploy_file_cpp'], cfg['trained_model'], 'prob')

    def decision_field(self):
        return self.cfg['decision_field']

    def output_field(self):
        return self.cfg['output_field']

    def predict(self, image_files):
        logging.info('%s: predicting %s' % (self.cfg['classifier_name'], image_files))
        result = {}
        if USE_PY:
            images = [caffe.io.load_image(f) for f in image_files]
            predictions = self.classifier.predict(images)
        else:
            predictions = [np.array(zcaffe.predict(self.classifier, f)) for f in image_files]
        for image_file, pred in zip(image_files, predictions):
            pred_label = pred.argmax()
            logging.info('%s: %s %s => %d' % (self.cfg['classifier_name'], image_file, pred, pred_label))
            result[image_file] = {
                self.decision_field(): bool(pred_label == FOUND),
                self.output_field(): str(pred),
            }
        return result
