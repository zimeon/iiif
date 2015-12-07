"""Test code for iiif.generators.check_5M."""
import unittest

from iiif.generators.check_5M import PixelGen

class TestAll(unittest.TestCase):

    def test01_size(self):
        gen = PixelGen()
        self.assertEqual( len(gen.size), 2 )
        self.assertTrue( int(gen.size[0]) > 4000000 )
