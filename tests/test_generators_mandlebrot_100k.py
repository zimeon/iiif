"""Test code for iiif.generators.mandlebrot_100k."""
import unittest
import cmath

from iiif.generators.mandlebrot_100k import PixelGen

class TestAll(unittest.TestCase):

    def test01_size(self):
        gen = PixelGen()
        self.assertEqual( len(gen.size), 2 )
        self.assertEqual( int(gen.size[0]), gen.size[0] )
        self.assertEqual( int(gen.size[1]), gen.size[1] )

    def test02_background_color(self):
        gen = PixelGen()
        self.assertEqual( len(gen.background_color), 3 )

    def test03_pixel(self):
        gen = PixelGen()
        self.assertEqual( gen.pixel(0,0), (0,50,100) )

    def test04_color(self):
        gen = PixelGen()
        self.assertEqual( gen.color(0), (0,50,100) )
        self.assertEqual( gen.color(999), (255,50,100) )

    def test05_mpixel(self):
        gen = PixelGen()
        # exceeds max_iter
        self.assertEqual( gen.mpixel( complex(0,0), 9999), None )
        # next iter
        self.assertEqual( gen.mpixel( complex(0.5,0.5), 0), None )

