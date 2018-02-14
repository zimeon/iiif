"""Test code for iiif.flask_utils.py."""
import unittest
import argparse
import flask
import os.path
import re  # needed because no assertRegexpMatches in 2.6
import json
from iiif.flask_utils import Config, html_page, top_level_index_page, identifiers, prefix_index_page, host_port_prefix, osd_page_handler, parse_authorization_header, parse_accept_header, add_shared_configs


class TestAll(unittest.TestCase):
    """Tests."""

    def setUp(self):
        """Create a test Flask app which we can use for context."""
        self.test_app = flask.Flask('TestApp')

    def test01_Config(self):
        """Test Config class."""
        c1 = Config()
        c1.a = 'a'
        c1.b = 'b'
        c2 = Config(c1)
        self.assertEqual(c2.a, 'a')
        self.assertEqual(c2.b, 'b')

    def test11_html_page(self):
        """Test HTML page wrapper."""
        html = html_page('TITLE', 'BODY')
        self.assertTrue('<h1>TITLE</h1>' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('BODY</body>' in html)  # FIXME - use assertIn when 2.6 dropped

    def test12_top_level_index_page(self):
        """Test top_level_index_page()."""
        c = Config()
        c.host = 'ex.org'
        c.prefixes = {'pa1a': 'pa1b', 'pa2a': 'pa2b'}
        html = top_level_index_page(c)
        self.assertTrue('ex.org' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('pa1a'in html)  # FIXME - use assertIn when 2.6 dropped

    def test13_identifiers(self):
        """Test identifiers()."""
        c = Config()
        # Generator case
        c.klass_name = 'gen'
        c.generator_dir = os.path.join(os.path.dirname(__file__), '../iiif/generators')
        ids = identifiers(c)
        self.assertTrue('sierpinski_carpet' in ids)  # FIXME - use assertIn when 2.6 dropped
        self.assertFalse('red-19000x19000' in ids)  # FIXME - use assertIn when 2.6 dropped
        # Non-gerenator case
        c = Config()
        c.klass_name = 'anything-not-gen'
        c.image_dir = os.path.join(os.path.dirname(__file__), '../testimages')
        ids = identifiers(c)
        self.assertFalse('sierpinski_carpet' in ids)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('red-19000x19000' in ids)  # FIXME - use assertIn when 2.6 dropped

    def test14_prefix_index_page(self):
        """Test prefix_index_page()."""
        c = Config()
        c.client_prefix = 'pfx'
        c.host = 'ex.org'
        c.api_version = '2.1'
        c.manipulator = 'pil'
        c.auth_type = 'none'
        c.include_osd = True
        c.klass_name = 'pil'
        c.image_dir = os.path.join(os.path.dirname(__file__), '../testimages')
        html = prefix_index_page(c)
        self.assertTrue('/pfx/' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertTrue('osd.html' in html)  # FIXME - use assertIn when 2.6 dropped
        # No OSD
        c.include_osd = False
        html = prefix_index_page(c)
        self.assertTrue('/pfx/' in html)  # FIXME - use assertIn when 2.6 dropped
        self.assertFalse('osd.html' in html)  # FIXME - use assertIn when 2.6 dropped

    def test15_host_port_prefix(self):
        """Test host_port_prefix()."""
        self.assertEqual(host_port_prefix('ex.org', 80, 'a'), 'http://ex.org/a')
        self.assertEqual(host_port_prefix('ex.org', 8888, 'a'), 'http://ex.org:8888/a')
        self.assertEqual(host_port_prefix('ex.org', 80, None), 'http://ex.org')

# Test Flask handlers

    def test20_osd_page_handler(self):
        """Test osd_page_handler() -- rather trivial check it runs with expected params."""
        c = Config()
        c.api_version = '2.1'
        with self.test_app.app_context():
            resp = osd_page_handler(c, 'an-unusual-id', 'a-prefix')
            html = resp.response[0]
            # Trivial tests on content...
            self.assertTrue(b'openseadragon.min.js' in html)
            self.assertTrue(b'an-unusual-id' in html)

    def test51_parse_authorization_header(self):
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

    def test52_parse_accept_header(self):
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

    def test60_add_shared_configs(self):
        """Test add_shared_configs() - just check it runs."""
        p = argparse.ArgumentParser()
        add_shared_configs(p)
        self.assertTrue('--include-osd' in p.format_help())
