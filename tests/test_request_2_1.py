"""Test encoding and decoding of iiif request URLs

Follows http://iiif.io/api/image/2.1/

This test includes a number of test cases beyond those given as examples
in the table in section 7 of the spec. See iiif_urltest_spec.py for the
set given in the spec.

Simeon Warner
  2015-05 - Working toward v2.1 spec
"""
import re
import unittest

from iiif.error import IIIFError
from iiif.request import IIIFRequest,IIIFRequestBaseURI

# Data for test. Format is
# name : [ {args}, 'canonical_url', 'alternate_form1', ... ]
# 
data  = {
    '00_params': [
        {'identifier':'id1', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default' },
        'id1/full/full/0/default'],
    '02_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'default', 'format':'jpg' },
        'id1/full/100,100/0/default.jpg'],
    '03_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'gray' },
        'id1/full/100,100/0/gray'],
    '04_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'quality':'gray', 'format':'tif' },
        'id1/full/100,100/0/gray.tif'],
    '05_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'size':'pct:100', 'rotation':'270', 'quality':'bitonal', 'format':'jpg'},
        'bb157hs6068/full/pct:100/270/bitonal.jpg',
        'bb157hs6068/full/pct%3A100/270/bitonal.jpg'],
    '06_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'size':'100,', 'rotation':'123.456', 'quality':'gray', 'format':'jpg'},
        'bb157hs6068/full/100,/123.456/gray.jpg'],
# ARKs from http://tools.ietf.org/html/draft-kunze-ark-00
# ark:sneezy.dopey.com/12025/654xz321
# ark:/12025/654xz321
    '21_ARK ': [
        {'identifier':'ark:sneezy.dopey.com/12025/654xz321', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default'},
        'ark:sneezy.dopey.com%2F12025%2F654xz321/full/full/0/default',
        'ark%3Asneezy.dopey.com%2F12025%2F654xz321/full/full/0/default'],
    '22_ARK ': [
        {'identifier':'ark:/12025/654xz321', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default'},
        'ark:%2F12025%2F654xz321/full/full/0/default',
        'ark%3A%2F12025%2F654xz321/full/full/0/default'],
# URNs from http://tools.ietf.org/html/rfc2141
# urn:foo:a123,456
    '31_URN ': [
        {'identifier':'urn:foo:a123,456', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default'},
        'urn:foo:a123,456/full/full/0/default',
        'urn%3Afoo%3Aa123,456/full/full/0/default'],
# URNs from http://en.wikipedia.org/wiki/Uniform_resource_name
# urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4
# ** note will get double encoding **
    '32_URN ': [
        {'identifier':'urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default'},
        'urn:sici:1046-8188(199501)13:1%253C69:FTTHBI%253E2.0.TX;2-4/full/full/0/default',
        'urn%3Asici%3A1046-8188(199501)13%3A1%253C69%3AFTTHBI%253E2.0.TX;2-4/full/full/0/default'],
# Extreme silliness
    '41_odd ': [
        {'identifier':'http://example.com/?54#a', 'region':'full', 'size':'full', 'rotation':'0', 'quality':'default'},
        'http:%2F%2Fexample.com%2F%3F54%23a/full/full/0/default',
        'http%3A%2F%2Fexample.com%2F?54#a/full/full/0/default'],
    # Info requests
    '50_info': [
        {'identifier':'id1', 'info':True, 'format':'json' },
        'id1/info.json'],
    }

class TestAll(unittest.TestCase):

    def test01_parse_region(self):
        r = IIIFRequest(api_version='2.1')
        r.region=None
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region='full'
        r.parse_region()
        self.assertTrue(r.region_full)
        self.assertFalse(r.region_square)
        r.region='square'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_square)
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
        r = IIIFRequest()
        r.region='pct:0,0,50,1000'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='pct:-10,0,50,100'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='pct:a,b,c,d'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='a,b,c,d'
        self.assertRaises( IIIFError, r.parse_region )
        # zero size
        r.region='0,0,0,100'
        self.assertRaises( IIIFError, r.parse_region )
        r.region='0,0,100,0'
        self.assertRaises( IIIFError, r.parse_region )

    def test03_parse_size(self):
        r = IIIFRequest()
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
        r = IIIFRequest()
        self.assertRaises( IIIFError, r.parse_size, ',0.0' )
        self.assertRaises( IIIFError, r.parse_size, '0.0,' )
        self.assertRaises( IIIFError, r.parse_size, '1.0,1.0' )
        self.assertRaises( IIIFError, r.parse_size, '1,1,1' )
        self.assertRaises( IIIFError, r.parse_size, 'bad-size')
        # bad pct size
        self.assertRaises( IIIFError, r.parse_size, 'pct:a')
        self.assertRaises( IIIFError, r.parse_size, 'pct:-1')
        # bad bang pixel size
        self.assertRaises( IIIFError, r.parse_size, '!1,')
        self.assertRaises( IIIFError, r.parse_size, '!,1')
        self.assertRaises( IIIFError, r.parse_size, '0,1')
        self.assertRaises( IIIFError, r.parse_size, '2,0')


    def test05_parse_rotation(self):
        r = IIIFRequest()
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
        # nothing supplied
        r.rotation = None
        r.parse_rotation()
        self.assertEqual(r.rotation_mirror, False)
        self.assertEqual(r.rotation_deg, 0.0)

    def test06_parse_rotation_bad(self):
        r = IIIFRequest()
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
        r = IIIFRequest()
        r.quality=None
        r.parse_quality()
        self.assertEqual(r.quality_val, 'default')
        r.quality='default'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'default')
        r.quality='bitonal'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'bitonal')
        r.quality='gray'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'gray')

    def test08_parse_quality_bad(self):
        r = IIIFRequest()
        r.quality='does_not_exist'
        self.assertRaises( IIIFError, r.parse_quality )
        # bad ones
        r.quality=''
        self.assertRaises( IIIFError, r.parse_quality )

    def test10_encode(self):
        for tname in sorted(data.keys()):
            tdata=data[tname]
            print(tname + "   " + self.pstr(data[tname][0]) + "  " + data[tname][1])
            iiif = IIIFRequest(**data[tname][0])
            self.assertEqual(iiif.url(),data[tname][1])
        print()
  
    def test11_decode(self):
        for tname in sorted(data.keys()):
            tdata=data[tname]
            pstr = self.pstr(data[tname][0])
            for turl in data[tname][1:]:
                iiif = IIIFRequest().split_url(turl)
                tstr = self.pstr(iiif.__dict__)
                print(tname + "   " + turl + " -> " + tstr)
                self.assertEqual(tstr,pstr)
        print()

    def test12_decode_except(self):
        self.assertRaises(IIIFRequestBaseURI, IIIFRequest().split_url, ("id"))
        self.assertRaises(IIIFRequestBaseURI, IIIFRequest().split_url, ("id%2Ffsdjkh"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id/"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id/bogus"))
        self.assertRaises(IIIFError, IIIFRequest().split_url, ("id1/all/270/!pct%3A75.23.jpg"))

    def test18_url(self):
        r = IIIFRequest()
        r.size = None 
        r.size_wh = [11,22]
        self.assertEqual( r.url(identifier='abc1'), 'abc1/full/11,22/0/default' )
        r.size_wh = [100,None]
        self.assertEqual( r.url(identifier='abc2'), 'abc2/full/100,/0/default' )
        r.size_wh = [None,999]
        self.assertEqual( r.url(identifier='abc3'), 'abc3/full/,999/0/default' )
        r.size_wh = None
        self.assertEqual( r.url(identifier='abc4'), 'abc4/full/full/0/default' )

    def test19_split_url(self):
        # mismatching baseurl
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFError, r.split_url, 'http://other.base.url/' )
        # matching baseurl, but bad request
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFRequestBaseURI , r.split_url, 'http://ex.org/a/b' )
        # matching baseurl, good request
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        r.identifier = None
        r.split_url('http://ex.org/a/b/full/full/0/native')
        self.assertEqual( r.identifier, 'b' )
        self.assertEqual( r.region, 'full' )
        self.assertEqual( r.size, 'full' )
        # matching baseurl, insert id, good request
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        r.identifier = 'b'
        r.split_url('http://ex.org/a/full/full/0/native')
        self.assertEqual( r.identifier, 'b' )
        self.assertEqual( r.region, 'full' )
        self.assertEqual( r.size, 'full' )
        # matching baseurl, too many segments
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFError, r.split_url, 'http://ex.org/a/1/2/3/4/5/6' )
        # api_version=1.0, format=xyz -> bad
        r = IIIFRequest(api_version='1.0')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFError, r.split_url, 'http://ex.org/a/b/info.xyz' )
        # api_version=2.1, format=xml -> bad
        r = IIIFRequest(api_version='2.1')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFError, r.split_url, 'http://ex.org/a/b/info.xml' )
        # api_version=2.1, format=xyz -> bad
        r = IIIFRequest(api_version='2.1')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises( IIIFError, r.split_url, 'http://ex.org/a/b/info.xyz' )

    def test20_parse_w_comma_h(self):
        r = IIIFRequest()
        self.assertEqual( r._parse_w_comma_h('1,2','a'), (1,2) )
        self.assertRaises( IIIFError, r._parse_w_comma_h, ',', 'region' )
        self.assertRaises( IIIFError, r._parse_w_comma_h, '1.0,1.0', 'size' )

    def test21_parse_non_negative_int(self):
        r = IIIFRequest()
        self.assertEqual( r._parse_non_negative_int('1','a'), (1) )
        self.assertRaises( ValueError, r._parse_non_negative_int, 'a', 'region' )
        self.assertRaises( ValueError, r._parse_non_negative_int, '-1', 'region' )

    def test22_str(self):
        # Simple tests of str()
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/'
        r.identifier = 'abc'
        # info
        r.info = True
        r.format = 'json'
        self.assertTrue( re.search(r'INFO request', str(r)) )
        self.assertTrue( re.search(r'format=json', str(r)) )
        # non-info
        r.info = False
        r.region = 'R'
        r.size = 'S'
        r.rotation = 'X'
        r.quality = 'Q'
        r.format ='jpg'
        self.assertFalse( re.search(r'INFO request', str(r)) )
        self.assertTrue( re.search(r'region=R', str(r)) )
        self.assertTrue( re.search(r'format=jpg', str(r)) )

    def pstr(self,p):
        s=''
        for k in ['identifier','region','size','rotation','default','info','format']:
            if k in p and p[k]:
                s += k+'='+str(p[k])+' '
        return(s)
