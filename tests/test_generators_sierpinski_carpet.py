"""Test code for iiif.generators.sierpinski_carpet."""
import unittest

from iiif.generators.sierpinski_carpet import PixelGen

class TestAll(unittest.TestCase):

    def test01_size(self):
        gen = PixelGen()
        self.assertEqual( len(gen.size), 2 )
        self.assertEqual( int(gen.size[0]), gen.size[0] )
        self.assertEqual( int(gen.size[1]), gen.size[1] )

    def test02_background_color(self):
        gen = PixelGen()
        self.assertEqual( len(gen.background_color), 3 )

    def test03_pizel(self):
        gen = PixelGen()
        self.assertEqual( gen.pixel(0,0), (0,0,0) )
        # n<=0
        self.assertEqual( gen.pixel(0,0,3), (0,0,0) )
        self.assertEqual( gen.pixel(1,1,3), None )
        # next iter
        self.assertEqual( gen.pixel(3,3,9), None )

