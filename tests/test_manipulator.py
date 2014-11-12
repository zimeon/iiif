"""Test code for null iiif.manipulator"""
import os
import shutil
import tempfile
import unittest

from iiif.manipulator import IIIFManipulator
from iiif.request import IIIFRequest
from iiif.error import IIIFError

class TestAll(unittest.TestCase):

    def test01_init(self):
        m = IIIFManipulator()
        self.assertEqual( m.api_version, '2.0' )
        m.cleanup()

    def test02_derive(self):
        m = IIIFManipulator()
        r = IIIFRequest()
        r.parse_url('id1/full/full/0/default')
        tmp = tempfile.mkdtemp()
        outfile = os.path.join(tmp,'testout.png')
        try:
            m.derive(srcfile='testimages/test1.png',
                     request=r, outfile=outfile);
            self.assertTrue( os.path.isfile(outfile) )
            self.assertEqual( os.path.getsize(outfile), 65810 )
        finally:
            shutil.rmtree(tmp) 
        # and where path to outfile must be created
        outfile = os.path.join(tmp,'a','b','testout.png')
        try:
            m.derive(srcfile='testimages/test1.png',
                     request=r, outfile=outfile);
            self.assertTrue( os.path.isfile(outfile) )
            self.assertEqual( os.path.getsize(outfile), 65810 )
        finally:
            shutil.rmtree(tmp) 

    def test03_do_first(self):
        m = IIIFManipulator()
        m.do_first()
        self.assertEqual( m.width, -1 )
        self.assertEqual( m.height, -1 )

    def test04_do_region(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.request.region_full=True
        m.do_region()
        # and now without region_full
        m.width=1
        m.height=1
        m.request.pct=200
        m.request.region_xywh=(1,1,1,1)
        m.request.region_full=False
        self.assertRaises( IIIFError, m.do_region )

    def test05_do_size(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.request.size_pct = 100
        m.request.size = '100'
        m.do_size()
        m.request.size_pct = None
        m.request.size = 'full'
        m.do_size()
        # and raise for not 100 or full
        m.request.size_pct = None
        m.request.size = '1,1'
        self.assertRaises( IIIFError, m.do_size )

    def test06_do_rotation(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.request.rotation_deg = 0.0
        m.do_rotation()
        # non 0.0 raises
        m.request.rotation_deg = 1.0
        self.assertRaises( IIIFError, m.do_rotation )

    def test07_do_quality(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.api_version = '1.1'
        m.request.quality = 'native'
        m.do_quality()
        m.api_version = '2.0'
        m.request.quality = 'default'
        m.do_quality()
        # raise it not appropriate no-op
        m.api_version = '1.1'
        m.request.quality = 'default'
        self.assertRaises( IIIFError, m.do_quality )
        m.api_version = '1.1'
        m.request.quality = 'other'
        self.assertRaises( IIIFError, m.do_quality )
        m.api_version = '2.0'
        m.request.quality = 'native'
        self.assertRaises( IIIFError, m.do_quality )
        m.api_version = '2.0'
        m.request.quality = 'other'
        self.assertRaises( IIIFError, m.do_quality )

    def test08_do_format(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.request.format = None
        m.srcfile = 'abc'
        m.do_format()
        self.assertEqual( m.outfile, m.srcfile )
        # failure to copy if srcfile and outfile specified same
        m.outfile = m.srcfile
        self.assertRaises( IIIFError, m.do_format )
        # any format specified -> raise
        m.request.format = 'something'
        self.assertRaises( IIIFError, m.do_format )
