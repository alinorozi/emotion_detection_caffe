# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

from zedge_config import get_options

# global constants
HADOOP_HOST = 'default'
HADOOP_PORT = 0

FOUND = 1
NOT_FOUND = 0

SUCCESS = 0
FAILURE = -1
STATUS = 'status'
STATUS_TXT = 'status_text'
COMMON_FIELDS = ['category', 'ctype', 'description', 'title', 'tags']


# timeout intervals (seconds)
CONN_TIMEOUT_INTERVALS = [30, 60, 120]
HTTP_TIMEOUT = 10

# global options
options = get_options('zedge_config.yaml')
WALLPAPERS_FIELD = options['wallpapers_field']
TEMP_FOLDER = options['temp_folder']
BAD_TERMS_FILE = options['bad_terms_file']
BAD_CATEGORIES_FILE = options['bad_categories_file']
TORNADO_PORT = options['tornado_port']
NUM_WORKERS = options['num_workers']
CPU_MODE = options['cpu_mode']
CLASSIFIER_SHAREABLE = options['classifier_shareable'][0]
IMAGE_CLASSIFIERS = [CLASSIFIER_SHAREABLE]
TEXT_EXPLICIT_FIELD = options['text_explicit_field']
USE_PY = (options['use_py'] != 0)
