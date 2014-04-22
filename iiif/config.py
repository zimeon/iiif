"""iiif configs

Goal is to have a sane set of default configs so that even if there
isn't entries in iiif.conf, or there are parameters missing, then something
useful will still happen.
"""
import ConfigParser
import os

I3F_CONF = 'etc/iiif.conf'

DEFAULTS = {
    'info' : {
        'tile_height': '256',
        'tile_width': '256',
        'scale_factors': '[1,2,4,8]',
        'formats': '[ "jpg", "png" ]',
        'qualities': '[ "native", "color" ]',
        },
    'test' : {
        'server_host': '',
        'server_port': '8000',
        'image_dir': 'testimages',
        'run_dummy': '1',
        'dummy_prefix': 'dummy',
        'run_pil': '1',
        'pil_prefix': 'pil',
        'run_netpbm': '',
        'netpbm_prefix': 'netpbm',
        },
}

class IIIFConfig(object):

    def __init__(self,conf_file=None):
        if (conf_file is None):
            root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            conf_file = os.path.join(root, I3F_CONF)
        self.conf = ConfigParser.ConfigParser()
        # set defaults
        for section in DEFAULTS.keys():
            self.conf.add_section(section)
            for option in DEFAULTS[section].keys():
                self.conf.set(section,option,DEFAULTS[section][option])
        # read config if present
        self.conf.read(conf_file)

    def get(self, section, option, raw=False, vars=None):
        """Wrapper for get(..) in ConfigParser"""
        return self.conf.get(section,option,raw,vars)
