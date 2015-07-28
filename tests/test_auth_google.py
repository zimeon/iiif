"""Test code for iiif.auth_google

See http://flask.pocoo.org/docs/0.10/testing/ for Flask notes
"""
from flask import Flask,request, make_response, redirect
import json
import re
import unittest

from iiif.auth_google import IIIFAuthGoogle

dummy_app = Flask('dummy')

class Struct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestAll(unittest.TestCase):

    def setUp(self):
        self.app = dummy_app.test_client()

    def tearDown(self):
        pass

    def test01_init(self):
        auth = IIIFAuthGoogle()
        self.assertTrue( re.match(r'\d+_',auth.cookie_prefix) )
        auth = IIIFAuthGoogle(cookie_prefix='abc')
        self.assertEqual( auth.cookie_prefix, 'abc')

    def test02_logout_service_description(self):
        auth = IIIFAuthGoogle()
        auth.logout_uri = 'xyz'
        lsd = auth.logout_service_description()
        self.assertEqual( lsd['profile'], 'http://iiif.io/api/auth/0/logout' )
        self.assertEqual( lsd['@id'], 'xyz' )
        self.assertEqual( lsd['label'], 'Logout from image server' )

    def test03_info_authn(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle()
            ia = auth.info_authn()
            self.assertEqual( ia, False )

    def test04_image_authn(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle()
            ia = auth.image_authn()
            self.assertEqual( ia, '' )

    def test05_login_handler(self):
        with dummy_app.test_request_context('/a_request'):
            config = Struct(host='a_host',port=None)
            auth = IIIFAuthGoogle()
            response = auth.login_handler(config=config,prefix='wxy')
            self.assertEqual( response.status_code, 302 )
            self.assertEqual( response.headers['Content-type'], 'text/html; charset=utf-8' )
            self.assertTrue( re.match(r'https://accounts.google.com/o/oauth2/auth', response.headers['Location']) )
            html = response.get_data()
            self.assertTrue( re.search('<h1>Redirecting...</h1>',html) )
 
    def test06_logout_handler(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle()
            response = auth.logout_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'text/html' )
            html = response.get_data()
            self.assertTrue( re.search(r'<script>window.close\(\);</script>',html) )

    def test07_access_token_handler(self):
        with dummy_app.test_request_context('/a_request'):
            auth = IIIFAuthGoogle()
            response = auth.access_token_handler()
            self.assertEqual( response.status_code, 200 )
            self.assertEqual( response.headers['Content-type'], 'application/json' )
            j = json.loads(response.get_data())
            self.assertEqual( j['error_description'], "No login details received" )
            self.assertEqual( j['error'], "client_unauthorized" )

    #def test07_home_handler(self):
    #    with dummy_app.test_request_context('/a_request'):
    #        auth = IIIFAuthGoogle()
    #        response = auth.home_handler()
    #        self.assertEqual( response.status_code, 200 )
    #        self.assertEqual( response.headers['Content-type'], 'text/html' )
