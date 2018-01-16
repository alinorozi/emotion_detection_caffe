# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import unittest
import json
import os
import re
try:
    from simplejson import loads, dumps
except ImportError:
    from json import loads, dumps
from httplib2 import Http

from zedge_common import *
from zedge_dict_check import DictionaryCheck
from zedge_hadoop import HadoopFile


CLASSIFIER_URL = 'http://0.0.0.0:' + str(WEBPY_PORT) + '/classifier'
TEST_DATA_DIR = 'test_data'

def copy_to_hadoop(image_files):
    for remote in image_files:
        h = HadoopFile(remote)
        if not h.exists():
            local = os.path.join(TEST_DATA_DIR, os.path.basename(remote))
            h.copy_from(local)


class ZedgeTests(unittest.TestCase):
    def setUp(self):
        nonoff_img = '/prod/convnet_wallpapers/test_data/9881755-nonoff.jpg'
        off_img = '/prod/convnet_wallpapers/test_data/713789-off.jpg'
        self.empty_img = '/prod/convnet_wallpapers/test_data/empty.jpg'
        copy_to_hadoop([nonoff_img, off_img, self.empty_img])

        wallpaper1 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{"id": 1, "rand": "2367621", '
            '"filename": "' + nonoff_img + '",'
            '"server": 2, "type": 43, "title": "Kozuf Mountain Resor speed", '
            '"category": 5, "date": 1361348203, "userid": "2127123", '
            '"ctype": 1, "user": "nakovmk", "tags": "kozuf,mountain,resort", '
            '"description": "Kozuf", "feature_vector": [-1]} ]}')

        wallpaper2 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{"id": 2, "rand": "5156799", '
            '"filename": "' + off_img + '",'
            '"server": 2, "type": 19, "title": "Aishwaryaa", "category": 7, '
            '"date": 1361349489, "userid": "21606817", "ctype": 1, '
            '"user": "___BrIzZzy____", "tags": "for,fun", '
            '"description": "Blank", "feature_vector": [-1]} ]}')

        wallpaper3 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{ "id": 3, "rand": "1785395", '
            '"filename": "' + nonoff_img + '",'
            '"server": 1, "type": 43, "title": "Snowboarding", "category": 14, '
            '"date": 1361348351, "userid": "2127123", "ctype": 1, '
            '"user": "nakovmk", "tags": "kozuf,mountain,nature,powder,snowboard", '
            '"description": "Snowboarding in some powder", "feature_vector": [-1]} ]}')

        wallpaper4 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{ "id": 3, "rand": "1785395", '
            '"filename": "' + nonoff_img + '",'
            '"server": 1, "type": 43, "title": "Snowboarding", "category": 7, '
            '"date": 1361348351, "userid": "2127123", "ctype": 1, '
            '"user": "nakovmk", "tags": "kozuf,mountain,nature,powder,snowboard,s E x", '
            '"description": "Snowboarding in some powder", "feature_vector": [-1]} ]}')

        wallpaper5 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{ "id": 3, "rand": "1785395", '
            '"filename": "' + nonoff_img + '",'
            '"server": 1, "type": 43, "title": "Snowboarding", "category": 7, '
            '"date": 1361348351, "userid": "2127123", "ctype": 1, '
            '"user": "nakovmk", "tags": "kozuf,mountain,nature,powder,snowboard", '
            '"description": "Snowboarding in some fucking powder", "feature_vector": [-1]} ]}')

        wallpaper6 = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{ "id": 3, "rand": "1785395", '
            '"filename": "' + nonoff_img + '",'
            '"server": 1, "type": 43, "title": "GODDAMN Snowboarding", "category": 7, '
            '"date": 1361348351, "userid": "2127123", "ctype": 1, '
            '"user": "nakovmk", "tags": "kozuf,mountain,nature,powder,snowboard", '
            '"description": "Snowboarding in some powder", "feature_vector": [-1]} ]}')

        self.empty_wallpaper = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{"id": 1, "rand": "2367621", '
            '"filename": "' + self.empty_img + '",'
            '"server": 2, "type": 43, "title": "Kozuf Mountain Resor", '
            '"category": 5, "date": 1361348203, "userid": "2127123", '
            '"ctype": 1, "user": "nakovmk", "tags": "kozuf,mountain,resort", '
            '"description": "Kozuf", "feature_vector": [-1]} ]}')

        # family unfriendly decision from the network/dictionary/category - True/False?
        self.wallpapers = [
            {'req': wallpaper1, 'convnet': False, 'cat': False, 'dic': False, FAMILY_UNFRIENDLY: False},
            {'req': wallpaper2, 'convnet': True,  'cat': False, 'dic': False, FAMILY_UNFRIENDLY: True},
            {'req': wallpaper3, 'convnet': False, 'cat': True,  'dic': False, FAMILY_UNFRIENDLY: True},
            {'req': wallpaper4, 'convnet': False, 'cat': False, 'dic': True,  FAMILY_UNFRIENDLY: True},
            {'req': wallpaper5, 'convnet': False, 'cat': False, 'dic': True,  FAMILY_UNFRIENDLY: True},
            {'req': wallpaper6, 'convnet': False, 'cat': False, 'dic': True,  FAMILY_UNFRIENDLY: True}
        ]

        self.dic_check = DictionaryCheck()

    def test_category_unfriendly(self):
        for w in self.wallpapers:
            data = w['req'][WALLPAPERS_GROUP][0]
            res, _ = self.dic_check.is_category_unfriendly(data['ctype'], data['category'])
            self.assertEqual(res, w['cat'])

    def test_dictionary_unfriendly(self):
        for w in self.wallpapers:
            data  = w['req'][WALLPAPERS_GROUP][0]
            title, _ = self.dic_check.is_dictionary_unfriendly(data['title'])
            tags, _ = self.dic_check.is_dictionary_unfriendly(data['tags'])
            descr, _ = self.dic_check.is_dictionary_unfriendly(data['description'])
            self.assertEqual(title or tags or descr, w['dic'])

    def test_family_unfriendly(self):
        for w in self.wallpapers:
            data  = w['req'][WALLPAPERS_GROUP][0]
            res, _ = self.dic_check.is_family_unfriendly(data)
            self.assertEqual(res, w['dic'] or w['cat'])

    def test_convnet(self):
        for w in self.wallpapers:
            req  = w['req']
            http = Http()
            resp, content = http.request(
                uri=CLASSIFIER_URL,
                method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8'},
                body=dumps(req).encode('utf-8'),
            )
            content = loads(content)
            filename = req[WALLPAPERS_GROUP][0]['filename']
            self.assertEqual(content[filename][STATUS], SUCCESS)
            self.assertEqual(content[filename][FAMILY_UNFRIENDLY], w[FAMILY_UNFRIENDLY])
            convnet_output = content[filename][FAMILY_UNFRIENDLY_OUTPUT]
            convnet_output = re.findall(r"[\d.]+", convnet_output)
            self.assertEqual(len(convnet_output), 4)
            offensive = (int(convnet_output[1]) == FOUND)
            self.assertEqual(offensive, w['convnet'])

    def test_badimage(self):
        req = self.empty_wallpaper
        http = Http()
        resp, content = http.request(
            uri=CLASSIFIER_URL,
            method='POST',
            headers={'Content-Type': 'application/json; charset=utf-8'},
            body=dumps(req).encode('utf-8'),
        )
        content = loads(content)
        self.assertEqual(content[self.empty_img][STATUS], FAILURE)

    def test_image_not_found(self):
        not_found = '/prod/convnet_wallpapers/asdfasdfasf.jpg'

        req = json.loads('{"' + WALLPAPERS_GROUP + '":[ '
            '{"id": 1, "rand": "2367621", '
            '"filename": "' + not_found + '",'
            '"server": 2, "type": 43, "title": "Kozuf Mountain Resor", '
            '"category": 5, "date": 1361348203, "userid": "2127123", '
            '"ctype": 1, "user": "nakovmk", "tags": "kozuf,mountain,resort", '
            '"description": "Kozuf", "feature_vector": [-1]} ]}')

        http = Http()
        resp, content = http.request(
            uri=CLASSIFIER_URL,
            method='POST',
            headers={'Content-Type': 'application/json; charset=utf-8'},
            body=dumps(req).encode('utf-8'),
        )
        content = loads(content)
        self.assertEqual(content[not_found][STATUS], FAILURE)


if __name__ == '__main__':
    unittest.main()

