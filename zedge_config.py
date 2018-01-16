# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# (c) 2013-2015 Zedge Inc.
#
# Author: Muhammad A. Norozi 
#         (ali@zedge.net)

import yaml

def get_options(config_file):
    return yaml.load(open(config_file))

if __name__ == '__main__':
    from pprint import PrettyPrinter
    pp = PrettyPrinter()

    cfg = get_options('zedge_config.yaml')
    pp.pprint(cfg)

    image_classifiers = cfg['image_classifiers']
    for c in image_classifiers:
        print c

