"""Test code for iiif/info.py for Image API v3.0 auth service descriptions.

See: https://github.com/IIIF/iiif.io/blob/image-auth/source/api/image/3.0/authentication.md
"""
import unittest
from .testlib.assert_json_equal_mixin import AssertJSONEqual
import json
from iiif.info import IIIFInfo
from iiif.auth import IIIFAuth


class TestAll(unittest.TestCase, AssertJSONEqual):
    """Tests."""

    def test01_empty_auth_defined(self):
        """Test empty auth."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.add_services(info)
        self.assertJSONEqual(info.as_json(validate=False),
            '{\n  "@context": "http://iiif.io/api/image/3/context.json", \n  "id": "http://example.com/i1", \n  "profile": "level1",\n  "protocol": "http://iiif.io/api/image", "type": "ImageService3"\n}')
        self.assertEqual(info.service, None)

    def test02_just_login(self):
        """Test just login."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.login_uri = 'http://example.com/login'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], "http://example.com/login")
        self.assertEqual(info.service['label'], "Login to image server")
        self.assertEqual(info.service['profile'],
                         "http://iiif.io/api/auth/1/login")

    def test03_login_and_logout(self):
        """Test login and logout."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.login_uri = 'http://example.com/login'
        auth.logout_uri = 'http://example.com/logout'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], "http://example.com/login")
        self.assertEqual(info.service['label'], "Login to image server")
        self.assertEqual(info.service['profile'],
                         "http://iiif.io/api/auth/1/login")
        svcs = info.service['service']
        self.assertEqual(svcs['@id'], "http://example.com/logout")
        self.assertEqual(svcs['label'], "Logout from image server")
        self.assertEqual(svcs['profile'], "http://iiif.io/api/auth/1/logout")

    def test04_login_and_client_id(self):
        """Test login and client id."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.login_uri = 'http://example.com/login'
        auth.client_id_uri = 'http://example.com/client_id'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], "http://example.com/login")
        self.assertEqual(info.service['label'], "Login to image server")
        self.assertEqual(info.service['profile'],
                         "http://iiif.io/api/auth/1/login")
        svcs = info.service['service']
        self.assertEqual(svcs['@id'], "http://example.com/client_id")
        self.assertEqual(svcs['profile'], "http://iiif.io/api/auth/1/clientId")

    def test05_login_and_access_token(self):
        """Test login and access token."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.login_uri = 'http://example.com/login'
        auth.access_token_uri = 'http://example.com/token'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], "http://example.com/login")
        self.assertEqual(info.service['label'], "Login to image server")
        self.assertEqual(info.service['profile'],
                         "http://iiif.io/api/auth/1/login")
        svcs = info.service['service']
        self.assertEqual(svcs['@id'], "http://example.com/token")
        self.assertEqual(svcs['profile'], "http://iiif.io/api/auth/1/token")

    def test06_full_set(self):
        """Test full set of auth services."""
        info = IIIFInfo(identifier="http://example.com/i1", api_version='3.0')
        auth = IIIFAuth()
        auth.name = "Whizzo!"
        auth.logout_uri = 'http://example.com/logout'
        auth.access_token_uri = 'http://example.com/token'
        auth.client_id_uri = 'http://example.com/clientId'
        auth.login_uri = 'http://example.com/login'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], "http://example.com/login")
        self.assertEqual(info.service['label'], "Login to Whizzo!")
        svcs = info.service['service']
        self.assertEqual(svcs[0]['@id'], "http://example.com/logout")
        self.assertEqual(svcs[1]['@id'], "http://example.com/clientId")
        self.assertEqual(svcs[2]['@id'], "http://example.com/token")
