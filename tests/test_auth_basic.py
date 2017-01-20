"""Test code for iiif.auth_basic.

See http://flask.pocoo.org/docs/0.10/testing/ for Flask notes.
"""
from flask import Flask, request, make_response, redirect
from werkzeug.datastructures import Headers
import base64
import json
import re
import unittest

from iiif.auth_basic import IIIFAuthBasic

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
        """Test inialization."""
        auth = IIIFAuthBasic()
        self.assertTrue(re.match(r'\d+_', auth.cookie_prefix))
        auth = IIIFAuthBasic(cookie_prefix='abc')
        self.assertEqual(auth.cookie_prefix, 'abc')

    def test02_logout_service_description(self):
        """Test logout_service_description."""
        auth = IIIFAuthBasic()
        auth.logout_uri = 'xyz'
        lsd = auth.logout_service_description()
        self.assertEqual(lsd['profile'], 'http://iiif.io/api/auth/1/logout')
        self.assertEqual(lsd['@id'], 'xyz')
        self.assertEqual(lsd['label'], 'Logout from image server (basic auth)')

    def test03_info_authn(self):
        """Test info_authn."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            ia = auth.info_authn()
            self.assertEqual(ia, False)

    def test04_image_authn(self):
        """Test image_authn."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            ia = auth.image_authn()
            self.assertEqual(ia, False)

    def test05_login_handler(self):
        """Test login_handler."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            response = auth.login_handler()
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers['Content-type'], 'text/html')
            html = response.get_data().decode('utf-8')  # data is bytes in python3
            self.assertEqual(html, '')
        # add good login params and check OK, window close
        h = Headers()
        h.add('Authorization', b'Basic ' +
              base64.b64encode(b'userpass:userpass'))
        with dummy_app.test_request_context('/a_request', headers=h):
            response = auth.login_handler()
            self.assertEqual(response.status_code, 200)
            html = response.get_data().decode('utf-8')
            self.assertTrue(
                re.search(
                    r'<script>window.close\(\);</script>',
                    html))
            set_cookie = response.headers['Set-Cookie']
            self.assertTrue(
                re.search(
                    auth.account_cookie_name +
                    '=valid-http-basic-login',
                    set_cookie))
        # add bad login params and check fail
        h = Headers()
        h.add('Authorization', b'Basic ' +
              base64.b64encode(b'userpass:bad-pass'))
        with dummy_app.test_request_context('/a_request', headers=h):
            response = auth.login_handler()
            self.assertEqual(response.status_code, 401)

    def test06_logout_handler(self):
        """Test logout_handler."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            response = auth.logout_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-type'], 'text/html')
            html = response.get_data().decode('utf-8')  # get_data is bytes in python3
            self.assertTrue(
                re.search(
                    r'<script>window.close\(\);</script>',
                    html))
