# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi
#         (ali@zedge.net)

import re
import json

from zedge_common import BAD_TERMS_FILE, BAD_CATEGORIES_FILE
from zedge_utils import generate_all_ngram

def convert_keys(dic):
    if not isinstance(dic, dict):
        return dic
    return dict((int(k), convert_keys(v)) for k, v in dic.items())

class DictionaryCheck:
    def __init__(self):
        self.bad_terms = json.load(open(BAD_TERMS_FILE))
        self.bad_categories = convert_keys(json.load(open(BAD_CATEGORIES_FILE)))

    def is_category_unfriendly(self, content_type, category):
        res = (content_type in self.bad_categories and
               category in self.bad_categories[content_type] and
               self.bad_categories[content_type][category])
        return res, 'category: ' + str(category) if res else ''

    def is_category_unfriendly_hash(self, check_hash):
        if 'ctype' in check_hash and 'category' in check_hash:
            return self.is_category_unfriendly(check_hash['ctype'], check_hash['category'])
        return False, ''

    def is_dictionary_unfriendly(self, check_str):
        ngrams = generate_all_ngram(check_str)
        for term, flag in self.bad_terms.items():
            term = term.lower()
            if term in ngrams:
                return True, term
        return False, ''

    def is_dictionary_unfriendly_hash(self, check_hash, field):
        if field in check_hash:
            return self.is_dictionary_unfriendly(check_hash[field])
        return False, ''

    def is_family_unfriendly(self, check_hash):
        res, txt = self.is_category_unfriendly_hash(check_hash)
        if res: return True, txt
        res, txt = self.is_dictionary_unfriendly_hash(check_hash, 'title')
        if res: return True, 'title: ' + txt
        res, txt = self.is_dictionary_unfriendly_hash(check_hash, 'tags')
        if res: return True, 'tags: ' + txt
        res, txt = self.is_dictionary_unfriendly_hash(check_hash, 'description')
        if res: return True, 'description: ' + txt
        return False, ''

    def __str__(self):
        return str(self.bad_terms) + '\t' + str(self.bad_categories)


if __name__ == '__main__':
    dic_check = DictionaryCheck()
    #print dic_check
    print dic_check.is_dictionary_unfriendly('s e x y')
    print dic_check.is_category_unfriendly(1, 14)

