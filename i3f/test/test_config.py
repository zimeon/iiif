"""Test for i3f/config.py"""
import unittest

from i3f.config import I3fConfig

class TestAll(unittest.TestCase):

    def test01_defaults(self):
        c = I3fConfig(conf_file='does_no_exist')
        self.assertEqual( c.get('info','tile_width'), '256')
        self.assertEqual( c.get('info','tile_height'), '256')
        self.assertEqual( c.get('info','scale_factors'), '[1,2,4,8]')

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
