"""Test for iiif/config.py"""
import unittest

from iiif.config import IIIFConfig

class TestAll(unittest.TestCase):

    def test01_defaults(self):
        c = IIIFConfig(conf_file='does_no_exist')
        self.assertEqual( c.get('info','tile_width'), '256')
        self.assertEqual( c.get('info','tile_height'), '256')
        self.assertEqual( c.get('info','scale_factors'), '[1,2,4,8]')

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
