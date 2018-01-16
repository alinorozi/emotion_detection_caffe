# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import re
import os
import logging
import subprocess as sp
import cPickle
from PIL import Image

PATTERN = "[^A-ZÆØÅa-zæøå0-9]+"
MIN_NGRAM = 1
MAX_NGRAM = 20

def concat(s1, s2):
    sep = '' if len(s1) == 0 else ' '
    return s1 + sep + str(s2)

def check_create_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

# hadoop crc file
def get_crc_filename(f):
    return os.path.join(os.path.dirname(f), '.' + os.path.basename(f) + '.crc')

def unpickle(file):
    f = open(file, 'rb')
    dic = cPickle.load(f)
    f.close()
    return dic

def dopickle(file, dic):
    f = open(file, 'wb')
    cPickle.dump(dic, f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()

def is_image_file(filename):
    name, ext = os.path.splitext(filename)
    return (ext in ['.png', '.jpg', '.jpeg'])

def is_empty(filename):
    stat = os.stat(filename)
    #print stat.st_size  # in bytes
    return stat.st_size < 100

def resize(filename):
    logging.debug('started resizing %s' % (filename))
    img = Image.open(filename)
    w, h = img.size
    ratio = float(min(w, h)) / 256.0
    new_w = int(w / ratio)
    new_h = int(h / ratio)
    img = img.resize((new_w, new_h), Image.ANTIALIAS)
    shift_w = 0
    shift_h = 0
    if new_w > new_h:
        shift_w = (new_w - new_h) / 2
    else:
        shift_h = (new_h - new_w) / 2
    img = img.crop((shift_w,shift_h,shift_w+256,shift_h+256))
    if img.size != (256, 256):
        raise Exception("cropped image's size should be (256,256) " + filename + " (%d,%d)" % (img.size[0],img.size[1]))
    img.save(filename, "JPEG", quality=100)
    logging.debug('finished resizing %s' % (filename))

def make_chunks(lst, chunk_size):
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

def generate_ngram(input_list, n):
    res = set()
    for i in range(len(input_list) - n + 1):
        res.add(' '.join(input_list[i:i+n]))
    return res

def generate_all_ngram(input):
    res = set()
    input_list = re.split(PATTERN, input.lower())
    for i in range(MIN_NGRAM, MAX_NGRAM + 1):
        for j in generate_ngram(input_list, i):
            res.add(j)
    return res
