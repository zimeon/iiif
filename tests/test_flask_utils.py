"""Test code for iiif.flask_utils.py."""
import unittest
import re  # needed because no assertRegexpMatches in 2.6
import json
from iiif.flask_utils import parse_authorization_header, parse_accept_header


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_parse_authorization_header(self):
        """Test parse_authorization_header."""
        # Garbage
        self.assertEqual(parse_authorization_header(''), None)
        self.assertEqual(parse_authorization_header('junk'), None)
        self.assertEqual(parse_authorization_header(
            'junk and more junk'), None)
        # Valid Basic auth, from <https://www.ietf.org/rfc/rfc2617.txt>
        self.assertEqual(parse_authorization_header('Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='),
                         {'type': 'basic', 'username': 'Aladdin', 'password': 'open sesame'})
        self.assertEqual(parse_authorization_header('bASiC QWxhZGRpbjpvcGVuIHNlc2FtZQ=='),
                         {'type': 'basic', 'username': 'Aladdin', 'password': 'open sesame'})
        # Valid Digest auth, from <https://www.ietf.org/rfc/rfc2617.txt>
        self.assertEqual(parse_authorization_header(
            'Digest username="Mufasa", '
            'realm="testrealm@host.com", '
            'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
            'uri="/dir/index.html", '
            'qop=auth, nc=00000001, cnonce="0a4f113b", '
            'response="6629fae49393a05397450978507c4ef1", '
            'opaque="5ccc069c403ebaf9f0171e9517f40e41"'),
            {'type': 'digest', 'username': 'Mufasa',
             'nonce': 'dcd98b7102dd2f0e8b11d0f600bfb0c093',
             'realm': 'testrealm@host.com', 'qop': 'auth',
             'cnonce': '0a4f113b', 'nc': '00000001',
             'opaque': '5ccc069c403ebaf9f0171e9517f40e41',
             'uri': '/dir/index.html',
             'response': '6629fae49393a05397450978507c4ef1'})

    def test02_parse_accept_header(self):
        """Test parse_accept_header."""
        accepts = parse_accept_header("text/xml")
        self.assertEqual(len(accepts), 1)
        self.assertEqual(accepts[0], ('text/xml', (), 1.0))
        accepts = parse_accept_header("text/xml;q=0.5")
        self.assertEqual(len(accepts), 1)
        self.assertEqual(accepts[0], ('text/xml', (), 0.5))
        accepts = parse_accept_header("text/xml;q=0.5, text/html;q=0.6")
        self.assertEqual(len(accepts), 2)
        self.assertEqual(accepts[0], ('text/html', (), 0.6))
        self.assertEqual(accepts[1], ('text/xml', (), 0.5))
