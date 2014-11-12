"""Test code for iiif/info.py"""
import unittest
import re #needed because no assertRegexpMatches in 2.6
import json
from iiif.info import IIIFInfo

class TestAll(unittest.TestCase):

    def test01_minmal(self):
        # Just do the trivial JSON test
        # ?? should this empty case raise and error instead?
        ir = IIIFInfo(identifier="http://example.com/i1")
        self.assertEqual( ir.as_json(validate=False), '{\n  "@context": "http://iiif.io/api/image/2/context.json", \n  "@id": "http://example.com/i1", \n  "profile": [\n    "http://iiif.io/api/image/2/level1.json"\n  ], \n  "protocol": "http://iiif.io/api/image"\n}' )
        ir.width=100
        ir.height=200
        self.assertEqual( ir.as_json(), '{\n  "@context": "http://iiif.io/api/image/2/context.json", \n  "@id": "http://example.com/i1", \n  "height": 200, \n  "profile": [\n    "http://iiif.io/api/image/2/level1.json"\n  ], \n  "protocol": "http://iiif.io/api/image", \n  "width": 100\n}' )

    def test02_scale_factor(self):
        ir = IIIFInfo(width=199,height=299,tile_width=100,tile_height=100,scale_factors=[1,2])
        #self.assertRegexpMatches( ir.as_json(validate=False), r'"scaleFactors": \[\s*1' ) #,\s*2\s*]' ) #no assertRegexpMatches in 2.6
        json = ir.as_json(validate=False)
        self.assertTrue( re.search(r'"width": 100',json) )
        self.assertTrue( re.search(r'"scaleFactors": \[\s*1',json) )

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

    def test10_read_example_from_spec(self):
        i = IIIFInfo()
        fh = open('test_info/2.0/info_from_spec.json')
        i.read(fh)
        self.assertEqual( i.context, "http://iiif.io/api/image/2/context.json" )
        self.assertEqual( i.id, "http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C" )
        self.assertEqual( i.protocol, "http://iiif.io/api/image" )
        self.assertEqual( i.width, 6000 )
        self.assertEqual( i.height, 4000 )
        self.assertEqual( i.sizes, [ {"width" : 150, "height" : 100},
                                     {"width" : 600, "height" : 400},
                                     {"width" : 3000, "height": 2000} ] )

    def test11_read_example_with_extra(self):
        i = IIIFInfo()
        fh = open('test_info/2.0/info_with_extra.json')
        i.read(fh)
        self.assertEqual( i.context, "http://iiif.io/api/image/2/context.json" )
        self.assertEqual( i.id, "http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C" )
        self.assertEqual( i.protocol, "http://iiif.io/api/image" )
        self.assertEqual( i.width, 6000 )
        self.assertEqual( i.height, 4000 )
        self.assertEqual( i.tiles, [{"width" : 512, "scaleFactors" : [1,2,4,8,16]}] )
        # and should have 1.1-like params too
        self.assertEqual( i.tile_width, 512 )
        self.assertEqual( i.scale_factors, [1,2,4,8,16] )
        self.assertEqual( i.profile, "http://iiif.io/api/image/2/level2.json" )

    def test12_read_unknown_context(self):
        i = IIIFInfo()
        fh = open('test_info/2.0/info_bad_context.json')
        self.assertRaises( Exception, i.read, fh )

    def test20_write_example_in_spec(self):
        i = IIIFInfo(
            id="http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C",
            #"protocol" : "http://iiif.io/api/image",
            width=6000,
            height=4000,
            sizes=[
                {"width" : 150, "height" : 100},
                {"width" : 600, "height" : 400},
                {"width" : 3000, "height": 2000}
                ],
            tiles=[
                {"width" : 512, "scaleFactors" : [1,2,4,8,16]}
                ],
            profile="http://iiif.io/api/image/2/level2.json",
            formats = [ "gif", "pdf" ],
            qualities = [ "color", "gray" ],
            supports = [ "canonicalLinkHeader", "rotationArbitrary", "profileLinkHeader", "http://example.com/feature/" ],
            service={
                "@context": "http://iiif.io/api/annex/service/physdim/1/context.json",
                "profile": "http://iiif.io/api/annex/service/physdim",
                "physicalScale": 0.0025,
                "physicalUnits": "in"
                }
            )
        reparsed_json = json.loads( i.as_json() )
        example_json = json.load( open('test_info/2.0/info_from_spec.json') )
        self.maxDiff = 4000
        self.assertEqual( reparsed_json, example_json )

    def test21_write_profile(self):
        i = IIIFInfo(
            id="http://example.org/svc/a",width=1,height=2,
            profile='pfl', formats=["fmt1", "fmt2"])
        j = json.loads( i.as_json() )
        self.assertEqual( len(j['profile']), 2 )
        self.assertEqual( j['profile'][0], 'pfl' )
        self.assertEqual( j['profile'][1], {'formats':['fmt1','fmt2']} )
        i = IIIFInfo(
            id="http://example.org/svc/a",width=1,height=2,
            profile='pfl', qualities=None)
        j = json.loads( i.as_json() )
        self.assertEqual( len(j['profile']), 1 )
        self.assertEqual( j['profile'][0], 'pfl' )
        i = IIIFInfo(
            id="http://example.org/svc/a",width=1,height=2,
            profile='pfl', qualities=['q1','q2','q0'])
        j = json.loads( i.as_json() )
        self.assertEqual( len(j['profile']), 2 )
        self.assertEqual( j['profile'][0], 'pfl' )
        self.assertEqual( j['profile'][1], {'qualities':['q1','q2','q0']} )
        i = IIIFInfo(
            id="http://example.org/svc/a",width=1,height=2,
            profile='pfl', supports=['a','b'])
        j = json.loads( i.as_json() )
        self.assertEqual( len(j['profile']), 2 )
        self.assertEqual( j['profile'][0], 'pfl' )
        self.assertEqual( j['profile'][1], {'supports':['a','b']} )
        i = IIIFInfo(
            id="http://example.org/svc/a",width=1,height=2,
            profile='pfl', formats=["fmt1", "fmt2"],
            qualities=['q1','q2','q0'], supports=['a','b'])
        j = json.loads( i.as_json() )
        self.assertEqual( len(j['profile']), 2 )
        self.assertEqual( j['profile'][0], 'pfl' )
        self.assertEqual( j['profile'][1]['formats'], ['fmt1','fmt2'] )
        self.assertEqual( j['profile'][1]['qualities'], ['q1','q2','q0'] )
        self.assertEqual( j['profile'][1]['supports'], ['a','b'] )
