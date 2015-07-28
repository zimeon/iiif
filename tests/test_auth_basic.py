"""Test code for iiif.auth_basic

See http://flask.pocoo.org/docs/0.10/testing/ for Flask notes
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

    def setUp(self):
        self.app = dummy_app.test_client()

    def tearDown(self):
        pass

    def test01_init(self):
        auth = IIIFAuthBasic()
        self.assertTrue( re.match(r'\d+_',auth.cookie_prefix) )
        auth = IIIFAuthBasic(cookie_prefix='abc')
        self.assertEqual( auth.cookie_prefix, 'abc')

    def test02_logout_service_description(self):
        auth = IIIFAuthBasic()
        auth.logout_uri = 'xyz'
        lsd = auth.logout_service_description()
        self.assertEqual( lsd['profile'], 'http://iiif.io/api/image/2/auth/logout' )
        self.assertEqual( lsd['@id'], 'xyz' )
        self.assertEqual( lsd['label'], 'Logout from image server' )

    def test03_info_authn(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            ia = auth.info_authn()
            self.assertEqual( ia, False )

    def test04_image_authn(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            ia = auth.image_authn()
            self.assertEqual( ia, '' )

    def test05_login_handler(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            response = auth.login_handler()
            self.assertEqual( response.status_code, 401 )
            self.assertEqual( response.headers['Content-type'], 'text/html' )
            html = response.get_data()
            self.assertEqual( html, '' )
        # add good login params and check OK, window close
        h = Headers()
        h.add('Authorization', 'Basic ' + base64.b64encode('userpass:userpass'))
        with dummy_app.test_request_context('/a_request', headers=h):
            response = auth.login_handler()
            self.assertEqual( response.status_code, 200 )
            html = response.get_data()
            self.assertTrue( re.search(r'<script>window.close\(\);</script>',html) )
            set_cookie = response.headers['Set-Cookie']
            self.assertTrue( re.search(auth.auth_cookie_name+'=valid-http-basic-login', set_cookie) )
        # add bad login params and check fail
        h = Headers()
        h.add('Authorization', 'Basic ' + base64.b64encode('userpass:bad-pass'))
        with dummy_app.test_request_context('/a_request', headers=h):
            response = auth.login_handler()
            self.assertEqual( response.status_code, 401 )

 
    def test06_logout_handler(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            response = auth.logout_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'text/html' )
            html = response.get_data()
            self.assertTrue( re.search(r'<script>window.close\(\);</script>',html) )

    def test07_access_token_handler(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthBasic()
            response = auth.access_token_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'application/json' )
            j = json.loads(response.get_data())
            self.assertEqual( j['error_description'], "No login details received" )
            self.assertEqual( j['error'], "client_unauthorized" )
        # add Authorization header, check we get token
        h = Headers()
        h.add('Authorization', 'Basic ' + base64.b64encode('userpass:userpass'))
        with dummy_app.test_request_context('/a_request', headers=h):
            auth = IIIFAuthBasic()
            response = auth.access_token_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'application/json' )
            j = json.loads(response.get_data())
            self.assertEqual( j['access_token'], "secret_token_here" ) #FIXME
            self.assertEqual( j['token_type'], "Bearer" )
            self.assertEqual( j['expires_in'], 3600 )
        # add callback but no Authorization header
        with dummy_app.test_request_context('/a_request?callback=CB'):
            auth = IIIFAuthBasic()
            response = auth.access_token_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'application/javascript' )
            # strip JavaScript wrapper and then check JSON
            js = response.get_data()
            self.assertTrue( re.match('CB\(.*\);',js) )
            j = json.loads(js.lstrip('CB(').rstrip(');'))
            self.assertEqual( j['error_description'], "No login details received" )
            self.assertEqual( j['error'], "client_unauthorized" )
