"""Test code for iiif.auth_google.

See http://flask.pocoo.org/docs/0.10/testing/ for Flask notes.
"""
from flask import Flask, request, make_response, redirect
from werkzeug.datastructures import Headers
import json
import mock
import re
import sys
import unittest

from iiif.auth_google import IIIFAuthGoogle

dummy_app = Flask('dummy')

# test client_secret_file
csf = 'tests/testdata/test_client_secret.json'


class Struct(object):
    """Class with properties created from **kwargs."""

    def __init__(self, **kwargs):
        """Initialize attributes with kwargs."""
        self.__dict__.update(kwargs)


class Readable(object):
    """Class supporting read() method to mock urlopen."""

    def __init__(self, value):
        """Initialize with supplied value."""
        self.value = value

    def read(self):
        """Return stored value."""
        return self.value


class TestAll(unittest.TestCase):
    """Tests."""

    def urlopen_name(self):
        """Name of urlopen for python2 or python3.

        As imported into iiif.auth_google, see:
        http://stackoverflow.com/questions/11351382/mock-patching-from-import-statement-in-python
        """
        return('iiif.auth_google.urlopen')

    def setUp(self):
        """Set up dummy app."""
        self.app = dummy_app.test_client()

    def tearDown(self):
        """Nop."""
        pass

    def test01_init(self):
        """Test initialize."""
        auth = IIIFAuthGoogle(client_secret_file=csf)
        self.assertTrue(re.match(r'\d+_', auth.cookie_prefix))
        auth = IIIFAuthGoogle(client_secret_file=csf, cookie_prefix='abc')
        self.assertEqual(auth.cookie_prefix, 'abc')
        self.assertEqual(auth.google_api_client_id, 'SECRET_CODE_537')
        self.assertEqual(auth.account_cookie_name, 'abcaccount')
        auth = IIIFAuthGoogle(
            client_secret_file='/does_not_exist',
            cookie_prefix='abcd')
        self.assertEqual(auth.cookie_prefix, 'abcd')
        self.assertEqual(auth.google_api_client_id, 'oops_missing_client_id')

    def test02_logout_service_description(self):
        """Test logout_service_description method."""
        auth = IIIFAuthGoogle(client_secret_file=csf)
        auth.logout_uri = 'xyz'
        lsd = auth.logout_service_description()
        self.assertEqual(lsd['profile'], 'http://iiif.io/api/auth/1/logout')
        self.assertEqual(lsd['@id'], 'xyz')
        self.assertEqual(
            lsd['label'],
            'Logout from image server (Google auth)')

    def test03_info_authn(self):
        """Test info_authn method."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            ia = auth.info_authn()
            self.assertEqual(ia, False)

    def test04_image_authn(self):
        """Test image_authn method."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            ia = auth.image_authn()
            self.assertEqual(ia, False)

    def test05_login_handler(self):
        """Test login_handler method."""
        with dummy_app.test_request_context('/a_request'):
            config = Struct(host='a_host', port=None)
            auth = IIIFAuthGoogle(client_secret_file=csf)
            response = auth.login_handler(config=config, prefix='wxy')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.headers['Content-type'],
                'text/html; charset=utf-8')
            self.assertTrue(
                re.match(
                    r'https://accounts.google.com/o/oauth2/auth',
                    response.headers['Location']))
            html = response.get_data().decode('utf-8')
            self.assertTrue(re.search('<h1>Redirecting...</h1>', html))

    def test06_logout_handler(self):
        """Test logout_handler method."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            response = auth.logout_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-type'], 'text/html')
            html = response.get_data().decode('utf-8')
            self.assertTrue(
                re.search(
                    r'<script>window.close\(\);</script>',
                    html))

    def test07_access_token_handler(self):
        """Test access_token_handler method."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            response = auth.access_token_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers['Content-type'],
                'application/json')
            j = json.loads(response.get_data().decode('utf-8'))
            self.assertEqual(
                j['description'],
                "No authorization details received")
            self.assertEqual(j['error'], "client_unauthorized")
        # add callback but no account cookie
        with dummy_app.test_request_context('/a_request?messageId=1234'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            response = auth.access_token_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers['Content-type'],
                'text/html')
            # Check HTML is postMessage, includes an error
            html = response.get_data().decode('utf-8')
            self.assertTrue(re.search(
                r'postMessage\(',
                html))
            self.assertTrue(re.search(
                r'"error"',
                html))
        # add an account cookie
        h = Headers()
        h.add('Cookie', 'lol_account=ACCOUNT_TOKEN')
        with dummy_app.test_request_context('/a_request', headers=h):
            auth = IIIFAuthGoogle(client_secret_file=csf, cookie_prefix='lol_')
            # stub token gen:
            auth._generate_random_string = lambda x: 'lkjhg'
            response = auth.access_token_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers['Content-type'],
                'application/json')
            j = json.loads(response.get_data().decode('utf-8'))
            self.assertEqual(j['accessToken'], 'lkjhg')
        # add an account cookie and a messageId
        h = Headers()
        h.add('Cookie', 'lol_account=ACCOUNT_TOKEN')
        with dummy_app.test_request_context('/a_request?messageId=2345', headers=h):
            auth = IIIFAuthGoogle(client_secret_file=csf, cookie_prefix='lol_')
            response = auth.access_token_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.headers['Content-type'],
                'text/html')
            # Check HTML is postMessage, includes messageId,
            # does not include an error
            html = response.get_data().decode('utf-8')
            self.assertTrue(re.search(
                r'postMessage\(',
                html))
            self.assertTrue(re.search(
                r'"messageId":\s*"2345"',
                html))
            self.assertFalse(re.search(
                r'"error"',
                html))

    def test08_home_handler(self):
        """Test home_handler method."""
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle(client_secret_file=csf)
            # Avoid actual calls to Google by mocking methods used by
            # home_handler()
            auth.google_get_token = mock.Mock(return_value='ignored')
            auth.google_get_data = mock.Mock(
                return_value={
                    'email': 'e@mail',
                    'name': 'a name'})
            response = auth.home_handler()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-type'], 'text/html')
            html = response.get_data().decode('utf-8')
            self.assertTrue(
                re.search(
                    r'<script>window.close\(\);</script>',
                    html))

    def test09_google_get_token(self):
        """Test google_get_token method."""
        with dummy_app.test_request_context('/a_request'):
            with mock.patch(self.urlopen_name(),
                            return_value=Readable(b'{"a":"b"}')):
                auth = IIIFAuthGoogle(client_secret_file=csf)
                config = Struct(host='a_host', port=None)
                j = auth.google_get_token(config, 'prefix')
                self.assertEqual(j, {'a': 'b'})

    def test10_google_get_data(self):
        """Test google_get_data method."""
        with dummy_app.test_request_context('/a_request'):
            with mock.patch(self.urlopen_name(),
                            return_value=Readable(b'{"c":"d"}')):
                auth = IIIFAuthGoogle(client_secret_file=csf)
                config = Struct(host='a_host', port=None)
                j = auth.google_get_data(config, {'access_token': 'TOKEN'})
                self.assertEqual(j, {'c': 'd'})
