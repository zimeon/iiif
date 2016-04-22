"""Test code for iiif.generators.check___59k."""
import unittest

from iiif.generators.check___59k import PixelGen

class TestAll(unittest.TestCase):

    def test01_size(self):
        gen = PixelGen()
        self.assertEqual( len(gen.size), 2 )
        self.assertTrue( int(gen.size[0]) > 59000 )
        self.assertTrue( int(gen.size[0]) < 60000 )
