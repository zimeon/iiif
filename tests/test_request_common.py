"""Test encoding/decoding of IIIF Image API URLs for all versions.

These tests apply to all versions of the IIIF Image API.

Simeon Warner, 2016-05...
"""
import re
import unittest

from iiif.error import IIIFError
from iiif.request import IIIFRequest, IIIFRequestError, IIIFRequestBaseURI


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_split_url(self):
        """Test split_url() method.

        For everything except the handling of extension type on
        info.json requests (where v1.0 allows XML), the behavior
        of split_url() is version independent.
        """
        # mismatching baseurl
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises(IIIFRequestError, r.split_url, 'http://other.base.url/')
        # matching baseurl, but bad request
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/a/'
        self.assertRaises(IIIFRequestBaseURI, r.split_url, 'http://ex.org/a/b')
        # matching baseurl, good request
        r = IIIFRequest(baseurl='http://ex.org/a/')
        r.identifier = None
        r.split_url('http://ex.org/a/b/full/full/0/native')
        self.assertEqual(r.identifier, 'b')
        self.assertEqual(r.region, 'full')
        self.assertEqual(r.size, 'full')
        # matching baseurl, insert id, good request
        r = IIIFRequest(baseurl='http://ex.org/a/')
        r.identifier = 'b'
        r.split_url('http://ex.org/a/full/full/0/native')
        self.assertEqual(r.identifier, 'b')
        self.assertEqual(r.region, 'full')
        self.assertEqual(r.size, 'full')
        # matching baseurl, too many segments
        r = IIIFRequest(baseurl='http://ex.org/a/')
        self.assertRaises(IIIFRequestError, r.split_url,
                          'http://ex.org/a/1/2/3/4/5/6')

    def test01_parse_w_comma_h(self):
        """Test w,h parsing."""
        r = IIIFRequest()
        self.assertEqual(r._parse_w_comma_h('1,2', 'a'), (1, 2))
        self.assertRaises(IIIFError, r._parse_w_comma_h, ',', 'region')
        self.assertRaises(IIIFError, r._parse_w_comma_h, '1.0,1.0', 'size')

    def test02_parse_non_negative_int(self):
        """Test parsing of non-negative integer."""
        r = IIIFRequest()
        self.assertEqual(r._parse_non_negative_int('1', 'a'), (1))
        self.assertRaises(ValueError,
                          r._parse_non_negative_int, 'a', 'region')
        self.assertRaises(ValueError,
                          r._parse_non_negative_int, '-1', 'region')

    def test03_str(self):
        """Simple tests of str() method."""
        r = IIIFRequest()
        r.baseurl = 'http://ex.org/'
        r.identifier = 'abc'
        # info
        r.info = True
        r.format = 'json'
        self.assertTrue(re.search(r'INFO request', str(r)))
        self.assertTrue(re.search(r'format=json', str(r)))
        # non-info
        r.info = False
        r.region = 'R'
        r.size = 'S'
        r.rotation = 'X'
        r.quality = 'Q'
        r.format = 'jpg'
        self.assertFalse(re.search(r'INFO request', str(r)))
        self.assertTrue(re.search(r'region=R', str(r)))
        self.assertTrue(re.search(r'format=jpg', str(r)))

    def test04_allow_slashes_in_identifier_munger(self):
        """Test request munger, list in, list out."""
        r = IIIFRequest()
        # Image requests
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'b', 'c', 'region', 'size', 'rotation', 'quality.ext']),
            ['a/b/c', 'region', 'size', 'rotation', 'quality.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'b', 'c', 'd', 'region', 'size', 'rotation', 'quality.ext']),
            ['a/b/c/d', 'region', 'size', 'rotation', 'quality.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'region', 'size', 'rotation', 'quality.ext']),
            ['a', 'region', 'size', 'rotation', 'quality.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['region', 'size', 'rotation', 'quality.ext']),
            ['region', 'size', 'rotation', 'quality.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['size', 'rotation', 'quality.ext']),
            ['size', 'rotation', 'quality.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['something']),
            ['something'])
        # Image Information requests
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'b', 'c', 'info.ext']),
            ['a/b/c', 'info.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'b', 'info.ext']),
            ['a/b', 'info.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['a', 'info.ext']),
            ['a', 'info.ext'])
        self.assertEqual(r._allow_slashes_in_identifier_munger(
            ['info.ext']),
            ['info.ext'])
