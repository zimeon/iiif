"""iiif configs

Goal is to have a sane set of default configs so that even if there
isn't entries in iiif.conf, or there are parameters missing, then something
useful will still happen.
"""
import ConfigParser
import os

IIIF_CONF = 'etc/iiif.conf'

DEFAULTS = {
    'info' : {
        'tile_height': '256',
        'tile_width': '256',
        'scale_factors': '[1,2,4,8]',
        'formats': '[ "jpg", "png" ]',
        'qualities': '[ "native", "color" ]',
        },
    'test_server' : {
        'server_host': '',
        'server_port': '8000',
        'image_dir': 'testimages',
        },
    'test1' : {
        'prefix': '1.1_dummy',
        'klass': 'dummy',
        'api_version': '1.1'
        },
    'test2' : {
        'prefix': '2.0_dummy',
        'klass': 'dummy',
        'api_version': '2.0'
        },
    'test3' : {
        'prefix': '1.1_pil',
        'klass': 'pil',
        'api_version': '1.0'
        },
    'test4' : {
        'prefix': '2.0_pil',
        'klass': 'pil',
        'api_version': '2.0'
        }
#    'test2' : {
#        'run_netpbm': '',
#        'netpbm_prefix': 'netpbm',
#        },
}

class IIIFConfig(object):

    def __init__(self,conf_file=None):
        if (conf_file is None):
            root = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            conf_file = os.path.join(root, IIIF_CONF)
        self.conf = ConfigParser.ConfigParser()
        # set defaults
        for section in DEFAULTS.keys():
            self.conf.add_section(section)
            for option in DEFAULTS[section].keys():
                self.conf.set(section,option,DEFAULTS[section][option])
        # read config if present
        self.conf.read(conf_file)

    def get_test_sections(self):
        """Return a list of test section names

        Will look at all section names that start test but are not test_server
        """
        test_sections = []
        for section in self.conf.sections():
            if (section.startswith('test') and section!='test_server'):
                test_sections.append(section)
        return(test_sections)

    def get(self, section, option, raw=False, vars=None):
        """Wrapper for get(..) in ConfigParser"""
        return self.conf.get(section,option,raw,vars)
