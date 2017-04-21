"""Test code for iiif.auth_kiosk.

See http://flask.pocoo.org/docs/0.10/testing/ for Flask notes.
"""
from flask import Flask, request, make_response, redirect
from werkzeug.datastructures import Headers
import base64
import json
import re
import unittest

from iiif.auth_kiosk import IIIFAuthKiosk

dummy_app = Flask('dummy')


class TestAll(unittest.TestCase):
    """Tests."""

    def setUp(self):
        """Set up dummy app."""
        self.app = dummy_app.test_client()

    def tearDown(self):
        """No op."""
        pass

    def test01_init(self):
        """Test initialization."""
        auth = IIIFAuthKiosk()
        self.assertEqual(auth.auth_pattern, 'kiosk')
        self.assertTrue(re.match(r'\d+_', auth.cookie_prefix))
        auth = IIIFAuthKiosk(cookie_prefix='abc')
        self.assertEqual(auth.cookie_prefix, 'abc')

    def test02_login_handler(self):
        """Test login_handler."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthKiosk()
            response = auth.login_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-type'], 'text/html')
            html = response.get_data().decode('utf-8')  # data is bytes in python3
            self.assertTrue(
                re.search(r'<script>window.close\(\);</script>', html))
            set_cookie = response.headers['Set-Cookie']
            self.assertTrue(
                re.search(auth.account_cookie_name + '=kiosk-null-ok;',
                          set_cookie))
