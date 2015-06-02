"""Test code for iiif/info.py for Image API v2.1 auth service descriptions

See: https://github.com/IIIF/iiif.io/blob/image-auth/source/api/image/2.1/authentication.md
"""
import unittest
import re #needed because no assertRegexpMatches in 2.6
import json
from iiif.info import IIIFInfo
from iiif.auth import IIIFAuth

class TestAll(unittest.TestCase):

    def test01_empty_auth_defined(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.add_services(info)
        self.assertEqual( info.as_json(validate=False), '{\n  "@context": "http://iiif.io/api/image/2/context.json", \n  "@id": "http://example.com/i1", \n  "profile": [\n    "http://iiif.io/api/image/2/level1.json"\n  ], \n  "protocol": "http://iiif.io/api/image"\n}' )
        self.assertEqual( info.service, None )

    def test02_just_login(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.login_uri = 'http://example.com/login'
        auth.add_services(info) 
        self.assertEqual( info.service['@id'], "http://example.com/login" )
        self.assertEqual( info.service['label'], "Login to image server" )
        self.assertEqual( info.service['profile'], "http://iiif.io/api/image/2/auth/login" )

    def test03_just_logout(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.logout_uri = 'http://example.com/logout'
        auth.add_services(info) 
        self.assertEqual( info.service['@id'], "http://example.com/logout" )
        self.assertEqual( info.service['label'], "Logout from image server" )
        self.assertEqual( info.service['profile'], "http://iiif.io/api/image/2/auth/logout" )

    def test04_just_client_id(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.client_id_uri = 'http://example.com/client_id'
        auth.add_services(info) 
        self.assertEqual( info.service['@id'], "http://example.com/client_id" )
        self.assertEqual( info.service['profile'], "http://iiif.io/api/image/2/auth/clientId" )

    def test05_just_access_token(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.access_token_uri = 'http://example.com/token'
        auth.add_services(info) 
        self.assertEqual( info.service['@id'], "http://example.com/token" )
        self.assertEqual( info.service['profile'], "http://iiif.io/api/image/2/auth/token" )

    def test06_full_set(self):
        info = IIIFInfo(identifier="http://example.com/i1", api_version='2.1')
        auth = IIIFAuth()
        auth.name = "Whizzo!"
        auth.logout_uri = 'http://example.com/logout'
        auth.access_token_uri = 'http://example.com/token'
        auth.client_id_uri = 'http://example.com/clientId'
        auth.login_uri = 'http://example.com/login'
        auth.add_services(info) 
        self.assertEqual( info.service[0]['@id'], "http://example.com/login" )
        self.assertEqual( info.service[0]['label'], "Login to Whizzo!" )
        self.assertEqual( info.service[1]['@id'], "http://example.com/logout" )
        self.assertEqual( info.service[2]['@id'], "http://example.com/clientId" )
        self.assertEqual( info.service[3]['@id'], "http://example.com/token" )


