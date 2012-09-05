#!/usr/bin/env python

"""Test encoding and decoding of i3f request URLs

Follows http://library.stanford.edu/iiif/image-api/ v0.2 dated "13 April 2012"

This test includes a number of test cases beyond those given as examples
in the table in section 7 of the spec. See i3f_urltest_spec.py for the
set given in the spec.

Simeon Warner - 2012-03-23, 2012-04-13
"""
import unittest

from i3f.error import I3fError
from i3f.request import I3fRequest

# Data for test. Format is
# name : [ {args}, 'canonical_url', 'alternate_form1', ... ]
# 
data  = {
    '00_params': [
        {'identifier':'id1', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native' },
        'id1/full/full/0/native'],
    '02_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'native', 'format':'jpg' },
        'id1/full/100,100/0/native.jpg'],
    '03_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'grey' },
        'id1/full/100,100/0/grey'],
    '04_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'grey', 'format':'tif' },
        'id1/full/100,100/0/grey.tif'],
    '05_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'size':'pct:100', 'rotation':'270', 'quality':'bitonal', 'format':'jpg'},
        'bb157hs6068/full/pct:100/270/bitonal.jpg',
        'bb157hs6068/full/pct%3A100/270/bitonal.jpg'],
    '06_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'size':'100,', 'rotation':'123.456', 'quality':'grey', 'format':'jpg'},
        'bb157hs6068/full/100,/123.456/grey.jpg'],
# ARKs from http://tools.ietf.org/html/draft-kunze-ark-00
# ark:sneezy.dopey.com/12025/654xz321
# ark:/12025/654xz321
    '21_ARK ': [
        {'identifier':'ark:sneezy.dopey.com/12025/654xz321', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native'},
        'ark:sneezy.dopey.com%2F12025%2F654xz321/full/full/0/native',
        'ark%3Asneezy.dopey.com%2F12025%2F654xz321/full/full/0/native'],
    '22_ARK ': [
        {'identifier':'ark:/12025/654xz321', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native'},
        'ark:%2F12025%2F654xz321/full/full/0/native',
        'ark%3A%2F12025%2F654xz321/full/full/0/native'],
# URNs from http://tools.ietf.org/html/rfc2141
# urn:foo:a123,456
    '31_URN ': [
        {'identifier':'urn:foo:a123,456', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native'},
        'urn:foo:a123,456/full/full/0/native',
        'urn%3Afoo%3Aa123,456/full/full/0/native'],
# URNs from http://en.wikipedia.org/wiki/Uniform_resource_name
# urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4
# ** note will get double encoding **
    '32_URN ': [
        {'identifier':'urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native'},
        'urn:sici:1046-8188(199501)13:1%253C69:FTTHBI%253E2.0.TX;2-4/full/full/0/native',
        'urn%3Asici%3A1046-8188(199501)13%3A1%253C69%3AFTTHBI%253E2.0.TX;2-4/full/full/0/native'],
# Extreme silliness
    '41_odd ': [
        {'identifier':'http://example.com/?54#a', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'native'},
        'http:%2F%2Fexample.com%2F%3F54%23a/full/full/0/native',
        'http%3A%2F%2Fexample.com%2F?54#a/full/full/0/native'],
    # Info requests
    '50_info': [
        {'identifier':'id1', 'info':True, 'format':'json' },
        'id1/info.json'],
    '51_info': [
        {'identifier':'id1', 'info':True, 'format':'xml' },
        'id1/info.xml'],
    }

class TestAll(unittest.TestCase):

    def test02_parse_region(self):
        print "parse_region tests..."
        r = I3fRequest()
        r.region=None
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region='full'
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region='0,1,90,100'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertFalse(r.region_pct)
        self.assertEqual(r.region_xywh, [0,1,90,100] )
        r.region='pct:2,3,91,99'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [2,3,91,99] )
        r.region='pct:10,10,50,50'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [10.0,10.0,50.0,50.0])
        r.region='pct:0,0,100,100'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [0.0,0.0,100.0,100.0])
        # bad ones
        r.region='pct:0,0,50,1000'
        self.assertRaises( I3fError, r.parse_region )
        r.region='pct:-10,0,50,100'
        self.assertRaises( I3fError, r.parse_region )

    def test02_parse_size(self):
        print "parse_size tests..."
        r = I3fRequest()
        r.size='pct:100'
        r.parse_size()
        self.assertEqual(r.size_pct, 100.0)
        self.assertFalse(r.size_bang)
        r.size='1,2'
        r.parse_size()
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (1,2))
        r.size='3,'
        r.parse_size()
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (3,None))
        r.size=',4'
        r.parse_size()
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (None,4))
        r.size='!5,6'
        r.parse_size()
        self.assertFalse(r.size_pct)
        self.assertTrue(r.size_bang)
        self.assertEqual(r.size_wh, (5,6))

    def test03_parse_rotation(self):
        print "parse_rotation tests..."
        r = I3fRequest()
        r.rotation='0'
        r.parse_rotation()
        self.assertEqual(r.rotation_deg, 0.0)
        r.rotation='0.0000'
        r.parse_rotation()
        self.assertEqual(r.rotation_deg, 0.0)
        r.rotation='180'
        r.parse_rotation()
        self.assertEqual(r.rotation_deg, 180.0)
        r.rotation='180'
        r.parse_rotation()
        self.assertEqual(r.rotation_deg, 180.0)
        # bad ones
        r.rotation='-1'
        self.assertRaises( I3fError, r.parse_rotation )
        r.rotation='-0.0000001'
        self.assertRaises( I3fError, r.parse_rotation )
        r.rotation='360.1'
        self.assertRaises( I3fError, r.parse_rotation )
        r.rotation='abc'
        self.assertRaises( I3fError, r.parse_rotation )

    def test04_parse_quality(self):
        print "parse_quality tests..."
        r = I3fRequest()
        r.quality=None
        r.parse_quality()
        self.assertEqual(r.quality_val, 'native')
        r.quality='native'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'native')
        r.quality='bitonal'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'bitonal')
        r.quality='grey'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'grey')
        # bad ones
        r.quality='does_not_exist'
        self.assertRaises( I3fError, r.parse_quality )
        # bad ones
        r.quality=''
        self.assertRaises( I3fError, r.parse_quality )


    def test1_encode(self):
        print "Encoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            print tname + "   " + self.pstr(data[tname][0]) + "  " + data[tname][1]
            i3f = I3fRequest(**data[tname][0])
            self.assertEqual(i3f.url(),data[tname][1])
        print
  
    def test2_decode(self):
        print "Decoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            pstr = self.pstr(data[tname][0])
            for turl in data[tname][1:]:
                i3f = I3fRequest().split_url(turl)
                tstr = self.pstr(i3f.__dict__)
                print tname + "   " + turl + " -> " + tstr
                self.assertEqual(tstr,pstr)
        print

    def test3_decode_except(self):
        self.assertRaises(I3fError, I3fRequest().split_url, ("bogus"))
        self.assertRaises(I3fError, I3fRequest().split_url, ("id1/all/270/!pct%3A75.23.jpg"))

    def pstr(self,p):
        s=''
        for k in ['identifier','region','size','rotation','native','info','format']:
            if k in p and p[k]:
                s += k+'='+str(p[k])+' '
        return(s)

        
# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
