"""Test encoding and decoding of iiif request URLs

Follows http://www-sul.stanford.edu/iiif/image-api/ v1.0 dated "10 August 2012"

This test includes a number of test cases beyond those given as examples
in the table in section 7 of the spec. See iiif_urltest_spec.py for the
set given in the spec.

Simeon Warner - 2012-03-23, 2012-04-13
"""
import unittest

from iiif.error import IIIFError
from iiif.request import IIIFRequest,IIIFRequestBaseURI

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
    }

class TestAll(unittest.TestCase):

    def test01_parse_region(self):
        r = IIIFRequest(api_version='1.1')
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

    def test02_parse_region_bad(self):
        r = IIIFRequest(api_version='1.1')
        r.region='pct:0,0,50,1000'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='pct:-10,0,50,100'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='square'
        self.assertRaises( IIIFError, r.parse_region )

    def test03_parse_size(self):
        r = IIIFRequest(api_version='1.1')
        r.parse_size('pct:100')
        self.assertEqual(r.size_pct, 100.0)
        self.assertFalse(r.size_bang)
        r.parse_size('1,2')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (1,2))
        r.parse_size('3,')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (3,None))
        r.parse_size(',4')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (None,4))
        r.parse_size('!5,6')
        self.assertFalse(r.size_pct)
        self.assertTrue(r.size_bang)
        self.assertEqual(r.size_wh, (5,6))

    def test04_parse_size_bad(self):
        r = IIIFRequest(api_version='1.1')
        self.assertRaises( IIIFError, r.parse_size, ',0.0' )
        self.assertRaises( IIIFError, r.parse_size, '0.0,' )
        self.assertRaises( IIIFError, r.parse_size, '1.0,1.0' )
        self.assertRaises( IIIFError, r.parse_size, '1,1,1' )

    def test05_parse_rotation(self):
        r = IIIFRequest(api_version='1.1')
        r.parse_rotation('0')
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 0.0)
        r.parse_rotation('0.0000')
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 0.0)
        r.parse_rotation('0.000001')
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 0.000001)
        r.parse_rotation('180')
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 180.0)
        r.parse_rotation('360')
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 0.0)
        r.parse_rotation('!0')
        self.assertEqual(r.rotation_mirror, True)
        self.assertEqual(r.rotation_deg, 0.0)
        r.parse_rotation('!0.000')
        self.assertEqual(r.rotation_mirror, True)
        self.assertEqual(r.rotation_deg, 0.0)
        r.parse_rotation('!123.45678')
        self.assertEqual(r.rotation_mirror, True)
        self.assertEqual(r.rotation_deg, 123.45678)

    def test06_parse_rotation_bad(self):
        r = IIIFRequest(api_version='1.1')
        r.rotation='-1'
        self.assertRaises( IIIFError, r.parse_rotation )
        r.rotation='-0.0000001'
        self.assertRaises( IIIFError, r.parse_rotation )
        r.rotation='360.0000001'
        self.assertRaises( IIIFError, r.parse_rotation )
        r.rotation='abc'
        self.assertRaises( IIIFError, r.parse_rotation )
        r.rotation='1!'
        self.assertRaises( IIIFError, r.parse_rotation )
        r.rotation='!!4'
        self.assertRaises( IIIFError, r.parse_rotation )

    def test07_parse_quality(self):
        r = IIIFRequest(api_version='1.1')
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

    def test08_parse_quality_bad(self):
        r = IIIFRequest(api_version='1.1')
        r.quality='does_not_exist'
        self.assertRaises( IIIFError, r.parse_quality )
        # bad ones
        r.quality=''
        self.assertRaises( IIIFError, r.parse_quality )

    def test10_encode(self):
        for tname in sorted(data.keys()):
            tdata=data[tname]
            print(tname + "   " + self.pstr(data[tname][0]) + "  " + data[tname][1])
            iiif = IIIFRequest(api_version='1.1',**data[tname][0])
            self.assertEqual(iiif.url(),data[tname][1])
        print('')
  
    def test11_decode(self):
        for tname in sorted(data.keys()):
            tdata=data[tname]
            pstr = self.pstr(data[tname][0])
            for turl in data[tname][1:]:
                iiif = IIIFRequest(api_version='1.1').split_url(turl)
                tstr = self.pstr(iiif.__dict__)
                print(tname + "   " + turl + " -> " + tstr)
                self.assertEqual(tstr,pstr)
        print('')

    def test12_decode_except(self):
        self.assertRaises(IIIFRequestBaseURI, IIIFRequest().split_url, ("id"))
        self.assertRaises(IIIFRequestBaseURI, IIIFRequest().split_url, ("id%2Ffsdjkh"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id/"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id/bogus"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id1/all/270/!pct%3A75.23.jpg"))

    def test20_parse_w_comma_h(self):
        r = IIIFRequest(api_version='1.1')
        self.assertEqual( r._parse_w_comma_h('1,2','a'), (1,2) )

    def test21_parse_w_comma_h_bad(self):
        r = IIIFRequest(api_version='1.1')
        self.assertRaises( IIIFError, r._parse_w_comma_h, '1.0,1.0', 'size' )

    def pstr(self,p):
        s=''
        for k in ['identifier','region','size','rotation','native','info','format']:
            if k in p and p[k]:
                s += k+'='+str(p[k])+' '
        return(s)

