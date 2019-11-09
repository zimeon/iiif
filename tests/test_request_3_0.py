"""Test encoding and decoding of IIIF request URLs.

Follows http://iiif.io/api/image/3.0/

This test includes a number of test cases beyond those given
as examples in the table in section 7 of the spec. See
test_request_spec_3_0.py for the set given in the spec.

Simeon Warner, 2015-05...
"""
import re

from iiif.error import IIIFError
from iiif.request import IIIFRequest, IIIFRequestError, IIIFRequestBaseURI
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
        """Parse region."""
        r = IIIFRequest(api_version='3.0')
        r.region = None
        r.parse_region()
        self.assertTrue(r.region_full)
        r.region = 'full'
        r.parse_region()
        self.assertTrue(r.region_full)
        self.assertFalse(r.region_square)
        r.region = 'square'
        r.parse_region()
        self.assertFalse(r.region_full)
        self.assertTrue(r.region_square)
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
        """Parse region."""
        r = IIIFRequest(api_version='3.0')
        r.region = 'pct:0,0,50,1000'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'pct:-10,0,50,100'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'pct:a,b,c,d'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'a,b,c,d'
        self.assertRaises(IIIFError, r.parse_region)
        # zero size
        r.region = '0,0,0,100'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = '0,0,100,0'
        self.assertRaises(IIIFError, r.parse_region)
        # bad  name
        r.region = '!square'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = 'square!'
        self.assertRaises(IIIFError, r.parse_region)
        r.region = ''
        self.assertRaises(IIIFError, r.parse_region)

    def test03_parse_size(self):
        """Parse size."""
        r = IIIFRequest(api_version='3.0')
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
        # 'max' is new in 3.0
        r = IIIFRequest(api_version='3.0')
        r.parse_size('max')
        self.assertFalse(r.size_full)
        self.assertTrue(r.size_max)
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (None, None))
        # '^' prefix is new in 3.0
        r = IIIFRequest(api_version='3.0')
        r.parse_size('^5000,')
        self.assertTrue(r.size_caret)
        self.assertFalse(r.size_max)
        self.assertFalse(r.size_pct)
        self.assertFalse(r.size_bang)
        self.assertEqual(r.size_wh, (5000, None))

    def test04_parse_size_bad(self):
        """Parse size - bad requests."""
        r = IIIFRequest(api_version='3.0')
        self.assertRaises(IIIFError, r.parse_size, ',0.0')
        self.assertRaises(IIIFError, r.parse_size, '0.0,')
        self.assertRaises(IIIFError, r.parse_size, '1.0,1.0')
        self.assertRaises(IIIFError, r.parse_size, '1,1,1')
        self.assertRaises(IIIFError, r.parse_size, 'bad-size')
        # bad pct size
        self.assertRaises(IIIFError, r.parse_size, 'pct:a')
        self.assertRaises(IIIFError, r.parse_size, 'pct:-1')
        # bad bang pixel size
        self.assertRaises(IIIFError, r.parse_size, '!1,')
        self.assertRaises(IIIFError, r.parse_size, '!,1')
        self.assertRaises(IIIFError, r.parse_size, '0,1')
        self.assertRaises(IIIFError, r.parse_size, '2,0')
        # full no longer allowed in 3.0
        self.assertRaises(IIIFError, r.parse_size, 'full')

    def test05_parse_rotation(self):
        """Parse rotation."""
        r = IIIFRequest(api_version='3.0')
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
        """Parse rotation - bad requests."""
        r = IIIFRequest(api_version='3.0')
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
        """Parse rotation."""
        r = IIIFRequest(api_version='3.0')
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
        """Parse quality - bad requests."""
        r = IIIFRequest(api_version='3.0')
        r.quality = 'does_not_exist'
        self.assertRaises(IIIFError, r.parse_quality)
        # bad ones
        r.quality = ''
        self.assertRaises(IIIFError, r.parse_quality)

    def test09_parse_format(self):
        """Test parse_format."""
        r = IIIFRequest(api_version='3.0')
        r.format = 'jpg'
        r.parse_format()
        r.format = 'something_else_Z134'
        r.parse_format()
        # Bad things
        r.format = 'no spaces allowed'
        self.assertRaises(IIIFRequestError, r.parse_format)
        r.format = '~'
        self.assertRaises(IIIFRequestError, r.parse_format)
        r.format = ''
        self.assertRaises(IIIFRequestError, r.parse_format)

    def test10_encode(self):
        """Encoding."""
        self.check_encoding(data, '3.0')

    def test11_decode(self):
        """Decoding."""
        self.check_decoding(data, '3.0')

    def test12_decode_good(self):
        """Decoding examples that should work."""
        r = IIIFRequest(api_version='3.0', baseurl='1.1_netpbm/a/')
        r.split_url('1.1_netpbm/a/b/full/full/0/default')
        self.assertEqual(r.identifier, 'b')
        # id with slashes in it
        r = IIIFRequest(api_version='3.0', allow_slashes_in_identifier=True)
        r.split_url('a/b/c/full/full/0/default')
        self.assertFalse(r.info)
        self.assertEqual(r.identifier, 'a/b/c')
        r = IIIFRequest(api_version='3.0', allow_slashes_in_identifier=True)
        r.split_url('a/b/info.json')
        self.assertTrue(r.info)
        self.assertEqual(r.identifier, 'a/b')

    def test13_decode_except(self):
        """Decoding exceptions."""
        self.assertRaises(IIIFRequestBaseURI,
                          IIIFRequest(api_version='3.0').split_url,
                          ("id"))
        self.assertRaises(IIIFRequestBaseURI,
                          IIIFRequest(api_version='3.0').split_url,
                          ("id%2Ffsdjkh"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='3.0').split_url,
                          ("id/"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='3.0').split_url,
                          ("id/bogus"))
        self.assertRaises(IIIFError,
                          IIIFRequest(api_version='3.0').split_url,
                          ("id1/all/270/!pct%3A75.23.jpg"))

    def test18_url(self):
        """Test url() method."""
        r = IIIFRequest(api_version='3.0')
        r.size = None
        r.size_wh = [11, 22]
        self.assertEqual(r.url(identifier='abc1'),
                         'abc1/full/11,22/0/default')
        r.size_wh = [100, None]
        self.assertEqual(r.url(identifier='abc2'),
                         'abc2/full/100,/0/default')
        r.size_wh = [None, 999]
        self.assertEqual(r.url(identifier='abc3'),
                         'abc3/full/,999/0/default')
        r.size_wh = None
        self.assertEqual(r.url(identifier='abc4'),
                         'abc4/full/full/0/default')
        r = IIIFRequest(api_version='3.0')
        r.size_full = True
        self.assertEqual(r.url(identifier='abc5'),
                         'abc5/full/full/0/default')
        r = IIIFRequest(api_version='3.0')
        r.size_max = True
        self.assertEqual(r.url(identifier='abc5'),
                         'abc5/full/max/0/default')

    def test19_split_url(self):
        """Test split_url() method.

        Most parts are common to all versions, except handling
        of info.json extensions.
        """
        # api_version=1.0, format=xyz -> bad
        r = IIIFRequest(api_version='1.0')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises(IIIFError, r.split_url,
                          'http://ex.org/a/b/info.xyz')
        # api_version=3.0, format=xml -> bad
        r = IIIFRequest(api_version='3.0')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises(IIIFError, r.split_url,
                          'http://ex.org/a/b/info.xml')
        # api_version=3.0, format=xyz -> bad
        r = IIIFRequest(api_version='3.0')
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises(IIIFError, r.split_url,
                          'http://ex.org/a/b/info.xyz')

    def test20_bad_response_codes(self):
        """Response codes."""
        for (path, code) in [("id/b", 400),
                             ("id/info.xml", 400),
                             ("id/b/c", 400),
                             ("id/b/c/d", 400),
                             ("id/full/full/0/default.jpg/extra", 400)]:
            got_code = None
            try:
                IIIFRequest(api_version='3.0').split_url(path)
            except IIIFError as e:
                got_code = e.code
            self.assertEqual(got_code, code,
                             "Bad code %s, expected %d, for path %s" %
                             (str(got_code), code, path))
