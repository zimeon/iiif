"""Test code for iiif/info.py"""
import unittest
import re #needed because no assertRegexpMatches in 2.6
from iiif.info import IIIFInfo

class TestAll(unittest.TestCase):

    def test01_minmal(self):
        # Just do the trivial JSON test
        # ?? should this empty case raise and error instead?
        ir = IIIFInfo(identifier="http://example.com/i1")
        self.assertEqual( ir.as_json(validate=False), '{\n  "@context": "http://iiif.io/api/image/2.0/context.json", \n  "@id": "http://example.com/i1", \n  "profile": "http://iiif.io/api/image/2/level1.json", \n  "protocol": "http://iiif.io/api/image"\n}' )
        ir.width=100
        ir.height=200
        self.assertEqual( ir.as_json(), '{\n  "@context": "http://iiif.io/api/image/2.0/context.json", \n  "@id": "http://example.com/i1", \n  "height": 200, \n  "profile": "http://iiif.io/api/image/2/level1.json", \n  "protocol": "http://iiif.io/api/image", \n  "width": 100\n}' )

    def test02_scale_factor(self):
        ir = IIIFInfo(width=1,height=2,scale_factors=[1,2])
        #self.assertRegexpMatches( ir.as_json(validate=False), r'"scale_factors": \[\s*1' ) #,\s*2\s*]' ) #no assertRegexpMatches in 2.6
        json = ir.as_json(validate=False)
        self.assertTrue( re.search(r'"scale_factors": \[\s*1',json) )

    def test03_array_vals(self):
        i = IIIFInfo()
        i.scale_factors = [1,2,3]
        self.assertEqual( i.scale_factors, [1,2,3] )
        i.set('scale_factors','[4,5,6]')
        self.assertEqual( i.scale_factors, [4,5,6] )

    def test04_conf(self):
        conf = { 'tile_width': 999, 'scale_factors': '[9,8,7]' }
        i = IIIFInfo(conf=conf)
        self.assertEqual( i.tile_width, 999 )
        self.assertEqual( i.scale_factors, [9,8,7] )

    def test05_level_and_profile(self):
        i = IIIFInfo()
        i.level = 0
        self.assertEqual( i.level, 0 )
        self.assertEqual( i.profile, "http://iiif.io/api/image/2/level0.json" )
        i.level = 2
        self.assertEqual( i.level, 2 )
        self.assertEqual( i.profile, "http://iiif.io/api/image/2/level2.json" )
        i.profile = "http://iiif.io/api/image/2/level1.json"
        self.assertEqual( i.level, 1 )
    
    def test06_validate(self):
        i = IIIFInfo()
        self.assertRaises( Exception, i.validate, () )
        i = IIIFInfo(identifier='a')
        self.assertRaises( Exception, i.validate, () )
        i = IIIFInfo(identifier='a',width=1,height=2)
        self.assertTrue( i.validate() )

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
