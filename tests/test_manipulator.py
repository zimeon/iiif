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
        m.do_region(None,None,None,None)
        # and now without region_full
        self.assertRaises( IIIFError, m.do_region, 1,1,1,1 )

    def test05_do_size(self):
        m = IIIFManipulator()
        m.do_size(None,None)
        # and raise for not 100 or full
        self.assertRaises( IIIFError, m.do_size, 10,10 )

    def test06_do_rotation(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        m.do_rotation(False,0.0)
        # mirror raises
        self.assertRaises( IIIFError, m.do_rotation, True,0.0 )
        # non 0.0 raises
        self.assertRaises( IIIFError, m.do_rotation, False,10.0 )

    def test07_do_quality(self):
        m = IIIFManipulator()
        m.api_version = '1.1'
        m.do_quality('native')
        m.api_version = '2.0'
        m.do_quality('default')
        # raise it not appropriate no-op
        m.api_version = '1.1'
        self.assertRaises( IIIFError, m.do_quality, 'default' )
        self.assertRaises( IIIFError, m.do_quality, 'other' )
        m.api_version = '2.0'
        self.assertRaises( IIIFError, m.do_quality, 'native' )
        self.assertRaises( IIIFError, m.do_quality, 'other' )

    def test08_do_format(self):
        m = IIIFManipulator()
        m.srcfile = 'abc'
        m.do_format(None)
        self.assertEqual( m.outfile, m.srcfile )
        # failure to copy if srcfile and outfile specified same
        m.outfile = m.srcfile
        self.assertRaises( IIIFError, m.do_format, None )
        # any format specified -> raise
        self.assertRaises( IIIFError, m.do_format, 'something' )

    def test09_do_last(self):
        m = IIIFManipulator()
        m.do_last() #nothing

    def test10_region_to_apply(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        # 4 None's for full
        m.request.region_full = True
        self.assertEqual( m.region_to_apply(), (None,None,None,None) )
        # pct:0,0,100,100 -> full
        m.request.region_full = False
        m.request.region_pct = True
        m.request.region_xywh = (0,0,100,100) 
        self.assertEqual( m.region_to_apply(), (None,None,None,None) )
        # negative size -> error
        m.request.region_full = False
        m.request.region_pct = None
        m.width = -1
        m.height = 1
        self.assertRaises( IIIFError, m.region_to_apply )
        m.width = 1
        m.height = -1
        self.assertRaises( IIIFError, m.region_to_apply )
        # pct no truncation
        m.width = 1000
        m.height = 2000
        m.request.region_pct = True
        m.request.region_xywh = (0,0,10,10)
        self.assertEqual( m.region_to_apply(), (0,0,100,200) )
        # pct with truncation
        m.width = 1000
        m.height = 2000
        m.request.region_pct = True
        m.request.region_xywh = (50,50,100,100)
        self.assertEqual( m.region_to_apply(), (500,1000,500,1000) )
        # x,y,w,h no truncation
        m.width = 1000
        m.height = 2000
        m.request.region_pct = None
        m.request.region_xywh = (10,20,200,400)
        self.assertEqual( m.region_to_apply(), (10,20,200,400) )
        # x,y,w,h truncate w
        m.width = 1000
        m.height = 2000
        m.request.region_pct = None
        m.request.region_xywh = (10,20,1001,400)
        self.assertEqual( m.region_to_apply(), (10,20,990,400) )
        # x,y,w,h truncate h
        m.width = 1000
        m.height = 2000
        m.request.region_pct = None
        m.request.region_xywh = (10,20,900,2400)
        self.assertEqual( m.region_to_apply(), (10,20,900,1980) )
        # pct works out same as full
        m.width = 1000
        m.height = 2000
        m.request.region_pct = True
        m.request.region_xywh = (0,0,100.0001,100.0001)
        self.assertEqual( m.region_to_apply(), (None,None,None,None) )
        # x,y,w,h works out same as full
        m.width = 1000
        m.height = 2000
        m.request.region_pct = None
        m.request.region_xywh = (0,0,2000,4000)
        self.assertEqual( m.region_to_apply(), (None,None,None,None) )

    def test11_size_to_apply(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        # full
        m.request.size_full = True
        self.assertEqual( m.size_to_apply(), (None,None) )
        # pct
        m.width = 1000
        m.height = 2000
        m.request.size_full = False
        m.request.size_pct = 10
        self.assertEqual( m.size_to_apply(), (100,200) )
        # pct > 100%
        m.width = 1000
        m.height = 2000
        m.request.size_pct = 101
        self.assertEqual( m.size_to_apply(), (1010,2020) )
        # !w,h
        m.request.size_pct = None
        m.request.size_bang = True
        m.request.size_wh = (100,400)
        self.assertEqual( m.size_to_apply(), (100,200) )
        # w,h
        m.request.size_bang = False
        m.request.size_wh = (100,400)
        self.assertEqual( m.size_to_apply(), (100,400) )
        # w,
        m.request.size_bang = False
        m.request.size_wh = (100,None)
        self.assertEqual( m.size_to_apply(), (100,200) )
        # ,h
        m.request.size_bang = False
        m.request.size_wh = (None,100)
        self.assertEqual( m.size_to_apply(), (50,100) )
        # ,h zero size
        m.request.size_bang = False
        m.request.size_wh = (None,0)
        self.assertRaises( IIIFError, m.size_to_apply )
        # w, -> full
        m.request.size_bang = False
        m.request.size_wh = (1000,None)
        self.assertEqual( m.size_to_apply(), (None,None) )

    def test12_rotation_to_apply(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        # 0
        m.request.rotation_deg=0
        self.assertEqual( m.rotation_to_apply(), (False,0) )
        # 90 and only90s
        m.request.rotation_deg=90
        self.assertEqual( m.rotation_to_apply(True), (False,90) )
        # 100
        m.request.rotation_deg=100
        self.assertEqual( m.rotation_to_apply(), (False,100) )
        # 100 and only90s
        m.request.rotation_deg=100
        self.assertRaises( IIIFError, m.rotation_to_apply, (True) )
        # 45 and mirror
        m.request.rotation_mirror=True
        m.request.rotation_deg=45
        self.assertEqual( m.rotation_to_apply(), (True,45) )
        # 45 and no-mirror
        self.assertRaises( IIIFError, m.rotation_to_apply, (True,True) )

    def test13_quality_to_apply(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        # v1.0,v1.1 none
        m.request.quality = None
        m.api_version = '1.0'
        self.assertEqual( m.quality_to_apply(), 'native' )
        m.api_version = '1.1'
        self.assertEqual( m.quality_to_apply(), 'native' )
        m.api_version = '2.0'
        self.assertEqual( m.quality_to_apply(), 'default' )
        # anything else
        m.request.quality = 'something'
        self.assertEqual( m.quality_to_apply(), 'something' )

    def test14_cleanup(self):
        m = IIIFManipulator()
        self.assertEqual( m.cleanup(), None )

    def test15_compliance_uri(self):
        # 1.0
        m = IIIFManipulator(api_version='1.0')
        self.assertEqual( m.compliance_uri, None )
        m.compliance_level = 0
        self.assertEqual( m.compliance_uri, 'http://library.stanford.edu/iiif/image-api/compliance.html#level0' )
        m.compliance_level = 1
        self.assertEqual( m.compliance_uri, 'http://library.stanford.edu/iiif/image-api/compliance.html#level1' )
        m.compliance_level = 2
        self.assertEqual( m.compliance_uri, 'http://library.stanford.edu/iiif/image-api/compliance.html#level2' )
        # 1.1
        m = IIIFManipulator(api_version='1.1')
        self.assertEqual( m.compliance_uri, None )
        m.compliance_level = 2
        self.assertEqual( m.compliance_uri, 'http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level2' )
        # 2.0
        m = IIIFManipulator(api_version='2.0')
        self.assertEqual( m.compliance_uri, None )
        m.compliance_level = 2
        self.assertEqual( m.compliance_uri, 'http://iiif.io/api/image/2/level2.json' )
        m.compliance_level = 99 #do we want this?
        self.assertEqual( m.compliance_uri, 'http://iiif.io/api/image/2/level99.json' )
        # unset
        m = IIIFManipulator(api_version=None)
        self.assertEqual( m.compliance_uri, None )
        m.compliance_level = 2
        self.assertEqual( m.compliance_uri, None )

