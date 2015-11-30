"""Test code for null iiif.manipulator_gen"""
import unittest
import tempfile
import os
import os.path

from PIL import Image

from iiif.error import IIIFError
from iiif.manipulator_gen import IIIFManipulatorGen
from iiif.request import IIIFRequest

class DummyGen(object):

    @property
    def size(self):
        return (256,256)

    @property
    def background_color(self):
        return (255,255,255)

    def pixel(self,x,y):
        if (x<256 and y<256):
            return (x,y,0)
        else:
            return None

class TestAll(unittest.TestCase):

    def test01_init(self):
        m = IIIFManipulatorGen()
        self.assertEqual( m.api_version, '2.0' )

    def test_do_first(self):
        m = IIIFManipulatorGen()
        # no image
        self.assertRaises( IIIFError, m.do_first )
        # add image, get size
        m.srcfile = 'check'
        self.assertEqual( m.do_first(), None )
        self.assertEqual( m.width, 19683 )
        self.assertEqual( m.height, 19683 )

    def test_do_region(self):
        m = IIIFManipulatorGen()
        m.width = 222
        m.height = 333
        m.do_region(None,None,None,None)
        self.assertEqual( m.rx, 0 )
        self.assertEqual( m.ry, 0 )
        self.assertEqual( m.rw, 222 )
        self.assertEqual( m.rh, 333 )
        m.do_region(1,2,3,4)
        self.assertEqual( m.rx, 1 )
        self.assertEqual( m.ry, 2 )
        self.assertEqual( m.rw, 3 )
        self.assertEqual( m.rh, 4 )

    def test_do_size(self):
        m = IIIFManipulatorGen()
        m.rx = 0
        m.ry = 0
        m.rw = 67
        m.rh = 89
        m.gen = DummyGen()
        m.do_size(None,None)
        self.assertEqual( m.sw, 67 )
        self.assertEqual( m.sh, 89 )
        m.do_size(101,102)
        self.assertEqual( m.sw, 101 )
        self.assertEqual( m.sh, 102 )

