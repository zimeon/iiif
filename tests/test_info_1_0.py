"""Test code for iiif/info.py for API version 1.0"""
import unittest
import re #needed because no assertRegexpMatches in 2.6
from iiif.info import IIIFInfo

class TestAll(unittest.TestCase):

    def assertJSONEqual(self, stra, strb):
        """Check JSON strings for equality.
        
        In python2.x the as_json method includes spaces after commas
        but before \n, this is not included in python3.x. Strip such
        spaces before doing the comparison.
        """
        a = re.sub(r',\s+',',',stra)
        b = re.sub(r',\s+',',',strb)
        self.assertEqual( a, b )

    def test01_minmal(self):
        # Just do the trivial JSON test
        ir = IIIFInfo(identifier="i1",api_version='1.0')
        self.assertJSONEqual( ir.as_json(validate=False), '{\n  "identifier": "i1", \n  "profile": "http://library.stanford.edu/iiif/image-api/compliance.html#level1"\n}' )
        ir.width=100
        ir.height=200
        self.assertJSONEqual( ir.as_json(), '{\n  "height": 200, \n  "identifier": "i1", \n  "profile": "http://library.stanford.edu/iiif/image-api/compliance.html#level1", \n  "width": 100\n}' )

    def test02_scale_factor(self):
        ir = IIIFInfo(width=1,height=2,scale_factors=[1,2],api_version='1.0')
        #self.assertRegexpMatches( ir.as_json(validate=False), r'"scale_factors": \[\s*1' ) #,\s*2\s*]' ) #no assertRegexpMatches in 2.6
        json = ir.as_json(validate=False)
        self.assertTrue( re.search(r'"scale_factors": \[\s*1',json) )

    def test03_array_vals(self):
        i = IIIFInfo(api_version='1.0')
        i.scale_factors = [1,2,3]
        self.assertEqual( i.scale_factors, [1,2,3] )
        i.set('scale_factors',[4,5,6])
        self.assertEqual( i.scale_factors, [4,5,6] )

    def test04_conf(self):
        conf = { 'tile_width': 999, 'scale_factors': [9,8,7] }
        i = IIIFInfo(conf=conf,api_version='1.0')
        self.assertEqual( i.tile_width, 999 )
        self.assertEqual( i.scale_factors, [9,8,7] )

    def test05_level_and_profile(self):
        i = IIIFInfo(api_version='1.0')
        i.level = 0
        self.assertEqual( i.level, 0 )
        self.assertEqual( i.profile, "http://library.stanford.edu/iiif/image-api/compliance.html#level0" )
        i.level = 2
        self.assertEqual( i.level, 2 )
        self.assertEqual( i.profile, "http://library.stanford.edu/iiif/image-api/compliance.html#level2" )
        i.profile = "http://library.stanford.edu/iiif/image-api/compliance.html#level1"
        self.assertEqual( i.level, 1 )
    
    def test06_validate(self):
        i = IIIFInfo(api_version='1.0')
        self.assertRaises( Exception, i.validate, () )
        i = IIIFInfo(identifier='a')
        self.assertRaises( Exception, i.validate, () )
        i = IIIFInfo(identifier='a',width=1,height=2)
        self.assertTrue( i.validate() )

    def test10_read_example_from_spec(self):
        i = IIIFInfo()
        fh = open('test_info/1.0/info_from_spec.json')
        i.read(fh,api_version='1.0')
        self.assertEqual( i.id, "1E34750D-38DB-4825-A38A-B60A345E591C" )
        self.assertEqual( i.profile, "http://library.stanford.edu/iiif/image-api/compliance.html#level0" )
        self.assertEqual( i.width, 6000 )
        self.assertEqual( i.height, 4000 )
        self.assertEqual( i.scale_factors, [1,2,4] )
        self.assertEqual( i.tile_width, 1024 )
        self.assertEqual( i.tile_height, 1024 )
        self.assertEqual( i.formats, ['jpg','png'] )
        self.assertEqual( i.qualities, ['native','grey'] )

    def test20_read_unknown_context(self):
        i = IIIFInfo()
        fh = open('test_info/1.0/info_bad_context.json')
        self.assertRaises( Exception, i.read, fh )
