"""Test encoding and decoding of iiif request URLs.

Follows http://iiif.io/api/image/2.0/

This test includes a number of test cases beyond those given as examples
in the table in section 7 of the spec. See test_request_spec.py for the
set given in the spec.

Simeon Warner - 2012-03-23, 2012-04-13
  2014-11-01 - Updated for v2.0 spec
"""

from iiif.error import IIIFError
from iiif.request import IIIFRequest, IIIFRequestBaseURI
from .testlib.request import TestRequests

# Data for test. Format is
# name : [ {args}, 'canonical_url', 'alternate_form1', ... ]
#
data = {
    '00_params': [
        {'identifier': 'id1', 'region': 'full', 'size': 'full',
            'rotation': '0', 'quality': 'default'},
        'id1/full/full/0/default'],
    '02_params': [
        {'identifier': 'id1', 'region': 'full', 'size': '100,100',
            'rotation': '0', 'quality': 'default', 'format': 'jpg'},
        'id1/full/100,100/0/default.jpg'],
    '03_params': [
        {'identifier': 'id1', 'region': 'full', 'size': '100,100',
            'rotation': '0', 'quality': 'gray'},
        'id1/full/100,100/0/gray'],
    '04_params': [
        {'identifier': 'id1', 'region': 'full', 'size': '100,100',
            'rotation': '0', 'quality': 'gray', 'format': 'tif'},
        'id1/full/100,100/0/gray.tif'],
    '05_params': [
        {'identifier': 'bb157hs6068', 'region': 'full', 'size': 'pct:100',
            'rotation': '270', 'quality': 'bitonal', 'format': 'jpg'},
        'bb157hs6068/full/pct:100/270/bitonal.jpg',
        'bb157hs6068/full/pct%3A100/270/bitonal.jpg'],
    '06_params': [
        {'identifier': 'bb157hs6068', 'region': 'full', 'size': '100,',
            'rotation': '123.456', 'quality': 'gray', 'format': 'jpg'},
        'bb157hs6068/full/100,/123.456/gray.jpg'],
    # ARKs from http://tools.ietf.org/html/draft-kunze-ark-00
    # ark:sneezy.dopey.com/12025/654xz321
    # ark:/12025/654xz321
    '21_ARK ': [
        {'identifier': 'ark:sneezy.dopey.com/12025/654xz321', 'region': 'full',
            'size': 'full', 'rotation': '0', 'quality': 'default'},
        'ark:sneezy.dopey.com%2F12025%2F654xz321/full/full/0/default',
        'ark%3Asneezy.dopey.com%2F12025%2F654xz321/full/full/0/default'],
    '22_ARK ': [
        {'identifier': 'ark:/12025/654xz321', 'region': 'full',
            'size': 'full', 'rotation': '0', 'quality': 'default'},
        'ark:%2F12025%2F654xz321/full/full/0/default',
        'ark%3A%2F12025%2F654xz321/full/full/0/default'],
    # URNs from http://tools.ietf.org/html/rfc2141
    # urn:foo:a123,456
    '31_URN ': [
        {'identifier': 'urn:foo:a123,456', 'region': 'full',
            'size': 'full', 'rotation': '0', 'quality': 'default'},
        'urn:foo:a123,456/full/full/0/default',
        'urn%3Afoo%3Aa123,456/full/full/0/default'],
    # URNs from http://en.wikipedia.org/wiki/Uniform_resource_name
    # urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4
    # ** note will get double encoding **
    '32_URN ': [
        {'identifier': 'urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4',
         'region': 'full', 'size': 'full', 'rotation': '0', 'quality': 'default'},
        'urn:sici:1046-8188(199501)13:1%253C69:FTTHBI%253E2.0.TX;2-4/full/full/0/default',
        'urn%3Asici%3A1046-8188(199501)13%3A1%253C69%3AFTTHBI%253E2.0.TX;2-4/full/full/0/default'],
    # Extreme silliness
    '41_odd ': [
        {'identifier': 'http://example.com/?54#a', 'region': 'full',
            'size': 'full', 'rotation': '0', 'quality': 'default'},
        'http:%2F%2Fexample.com%2F%3F54%23a/full/full/0/default',
        'http%3A%2F%2Fexample.com%2F?54#a/full/full/0/default'],
    # Info requests
    '50_info': [
        {'identifier': 'id1', 'info': True, 'format': 'json'},
        'id1/info.json'],
}


class TestAll(TestRequests):
    """Tests."""

    def test01_parse_region(self):
        """Region."""
        r = IIIFRequest()
        r.region = None
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region = 'full'
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region = '0,1,90,100'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertFalse(r.region_pct)
        self.assertEqual(r.region_xywh, [0, 1, 90, 100])
        r.region = 'pct:2,3,91,99'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [2, 3, 91, 99])
        r.region = 'pct:10,10,50,50'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [10.0, 10.0, 50.0, 50.0])
        r.region = 'pct:0,0,100,100'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_pct)
        self.assertEqual(r.region_xywh, [0.0, 0.0, 100.0, 100.0])

    def test02_parse_region_bad(self):
        """Bad regions."""
        r = IIIFRequest()
        r.region = 'pct:0,0,50,1000'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'pct:-10,0,50,100'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'square'
        self.assertRaises(IIIFError, r.parse_region)

    def test03_parse_size(self):
        """Size."""
        r = IIIFRequest()
        r.parse_size('pct:100')
        self.assertEqual(r.size_pct, 100.0)
        self.assertFalse(r.size_bang)
        r.parse_size('1,2')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (1, 2))
        r.parse_size('3,')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (3, None))
        r.parse_size(',4')
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (None, 4))
        r.parse_size('!5,6')
        self.assertFalse(r.size_pct)
        self.assertTrue(r.size_bang)
        self.assertEqual(r.size_wh, (5, 6))

    def test04_parse_size_bad(self):
        """Bad sizes."""
        r = IIIFRequest()
        self.assertRaises(IIIFError, r.parse_size, ',0.0')
        self.assertRaises(IIIFError, r.parse_size, '0.0,')
        self.assertRaises(IIIFError, r.parse_size, '1.0,1.0')
        self.assertRaises(IIIFError, r.parse_size, '1,1,1')
        # 'max' not allowed in 2.0, introduced in 2.1
        self.assertRaises(IIIFError, r.parse_size, 'max')

    def test05_parse_rotation(self):
        """Rotation."""
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

    def test06_parse_rotation_bad(self):
        """Bad rotation."""
        r = IIIFRequest()
        r.rotation = '-1'
        self.assertRaises(IIIFError, r.parse_rotation)
        r.rotation = '-0.0000001'
        self.assertRaises(IIIFError, r.parse_rotation)
        r.rotation = '360.0000001'
        self.assertRaises(IIIFError, r.parse_rotation)
        r.rotation = 'abc'
        self.assertRaises(IIIFError, r.parse_rotation)
        r.rotation = '1!'
        self.assertRaises(IIIFError, r.parse_rotation)
        r.rotation = '!!4'
        self.assertRaises(IIIFError, r.parse_rotation)

    def test07_parse_quality(self):
        """Quality."""
        r = IIIFRequest()
        r.quality = None
        r.parse_quality()
        self.assertEqual(r.quality_val, 'default')
        r.quality = 'default'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'default')
        r.quality = 'bitonal'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'bitonal')
        r.quality = 'gray'
        r.parse_quality()
        self.assertEqual(r.quality_val, 'gray')

    def test08_parse_quality_bad(self):
        """Bad quality."""
        r = IIIFRequest()
        r.quality = 'does_not_exist'
        self.assertRaises(IIIFError, r.parse_quality)
        # bad ones
        r.quality = ''
        self.assertRaises(IIIFError, r.parse_quality)

    def test10_encode(self):
        """Encoding."""
        self.check_encoding(data, '2.0')

    def test11_decode(self):
        """Decoding."""
        self.check_decoding(data, '2.0')

    def test12_decode_except(self):
        """Decoding exceptions."""
        self.assertRaises(IIIFRequestBaseURI,
                          IIIFRequest(api_version='2.0').split_url,
                          ("id"))
        self.assertRaises(IIIFRequestBaseURI,
                          IIIFRequest(api_version='2.0').split_url,
                          ("id%2Ffsdjkh"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='2.0').split_url,
                          ("id/"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='2.0').split_url,
                          ("id/bogus"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='2.0').split_url,
                          ("id1/all/270/!pct%3A75.23.jpg"))

    def test22_parse_response_codes(self):
        """Response codes."""
        r = IIIFRequest()
        for (path, code) in [("a/b/c", 400),
                             ("a/b/full/full/0/default.jpg", 404)]:
            got_code = None
            try:
                IIIFRequest().split_url(path)
            except IIIFError as e:
                got_code = e.code
            self.assertEqual(got_code, code, "Bad code %d, expected %d, for path %s" % (
                got_code, code, path))
