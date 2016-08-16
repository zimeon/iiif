"""Test code for iiif.auth."""
import json
import re
import unittest

from iiif.auth import IIIFAuth
from iiif.info import IIIFInfo


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_init(self):
        """Test initialization with params and cookie prefix."""
        auth = IIIFAuth()
        self.assertEqual(auth.profile_base, 'http://iiif.io/api/auth/0/')
        self.assertEqual(auth.name, "image server")
        auth = IIIFAuth(cookie_prefix='abc_')
        self.assertEqual(auth.cookie_prefix, 'abc_')
        self.assertEqual(auth.account_cookie_name, 'abc_account')
        self.assertEqual(auth.auth_cookie_name, 'abc_loggedin')

    def test02_set_cookie_prefix(self):
        """Test set_cookie_prefix."""
        auth = IIIFAuth()
        self.assertTrue(re.match(r'\d{6}_$', auth.cookie_prefix))
        auth.set_cookie_prefix()
        self.assertTrue(re.match(r'\d{6}_$', auth.cookie_prefix))
        auth.set_cookie_prefix('ghi')
        self.assertEqual(auth.cookie_prefix, 'ghi')

    def test03_add_services(self):
        """Test add_services."""
        info = IIIFInfo()
        auth = IIIFAuth()
        self.assertEqual(info.service, None)
        # first just login
        auth.add_services(info)
        self.assertEqual(info.service, None)
        auth.login_uri = 'Xlogin'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], 'Xlogin')
        # then login and logout
        info = IIIFInfo()
        auth = IIIFAuth()
        auth.login_uri = 'Xlogin'
        auth.logout_uri = 'Ylogout'
        auth.add_services(info)
        self.assertEqual(info.service['service']['@id'], 'Ylogout')
        # now add all, check we have all @ids in service description
        info = IIIFInfo()
        auth = IIIFAuth()
        auth.login_uri = 'Zlogin'
        auth.logout_uri = 'Zlogout'
        auth.client_id_uri = 'Zclient'
        auth.access_token_uri = 'Ztoken'
        auth.add_services(info)
        self.assertEqual(info.service['@id'], 'Zlogin')
        self.assertEqual(len(info.service['service']), 3)
        ids = set([e['@id'] for e in info.service['service']])
        self.assertEqual(
            ids, set([auth.logout_uri, auth.client_id_uri, auth.access_token_uri]))

    def test04_login_service_description(self):
        """Test login_service_description."""
        auth = IIIFAuth()
        lsd = auth.login_service_description()
        self.assertEqual(lsd['profile'], 'http://iiif.io/api/auth/0/login')
        auth.login_uri = 'id1'
        auth.profile_base = 'http://pb1/'
        auth.access_token_uri = 'id1access'
        lsd = auth.login_service_description()
        self.assertEqual(lsd['@id'], 'id1')
        self.assertEqual(lsd['profile'], 'http://pb1/login')
        # Check for embedded access token service description
        self.assertEqual(len(lsd['service']), 1)
        self.assertEqual(lsd['service'][0]['@id'], 'id1access')
        self.assertEqual(lsd['service'][0]['profile'], 'http://pb1/token')
        # Add in client id and logout services
        auth.client_id_uri = 'id1client_id'
        auth.logout_uri = 'id1logout'
        lsd = auth.login_service_description()
        self.assertEqual(lsd['@id'], 'id1')
        self.assertEqual(lsd['profile'], 'http://pb1/login')
        # Check for embedded client id and logout service descriptions
        self.assertEqual(len(lsd['service']), 3)
        self.assertEqual(lsd['service'][1]['@id'], 'id1client_id')
        self.assertEqual(lsd['service'][2]['@id'], 'id1logout')

    def test05_logout_service_description(self):
        """Test logout_service_description."""
        auth = IIIFAuth()
        auth.logout_uri = 'id2'
        auth.profile_base = 'http://pb2/'
        lsd = auth.logout_service_description()
        self.assertEqual(lsd['@id'], 'id2')
        self.assertEqual(lsd['profile'], 'http://pb2/logout')

    def test06_client_id_service_description(self):
        """Test client_id_service_description."""
        auth = IIIFAuth()
        auth.client_id_uri = 'id3'
        auth.profile_base = 'http://pb3/'
        lsd = auth.client_id_service_description()
        self.assertEqual(lsd['@id'], 'id3')
        self.assertEqual(lsd['profile'], 'http://pb3/clientId')

    def test07_access_token_service_description(self):
        """Test access_token_service_description."""
        auth = IIIFAuth()
        auth.access_token_uri = 'id4'
        auth.profile_base = 'http://pb4/'
        lsd = auth.access_token_service_description()
        self.assertEqual(lsd['@id'], 'id4')
        self.assertEqual(lsd['profile'], 'http://pb4/token')

    def test08_scheme_host_port_prefix(self):
        """Test URI building with scheme_host_port_prefix."""
        auth = IIIFAuth()
        self.assertEqual(
            auth.scheme_host_port_prefix('sc', 'x', '9', 'z'),
            'sc://x:9/z')
        self.assertEqual(
            auth.scheme_host_port_prefix(host='x', prefix='z'),
            'http://x/z')
        self.assertEqual(
            auth.scheme_host_port_prefix(host='yy'),
            'http://yy')
        self.assertEqual(
            auth.scheme_host_port_prefix(host='yy', port=80),
            'http://yy')
        self.assertEqual(
            auth.scheme_host_port_prefix(host='yy', port=81, prefix='x'),
            'http://yy:81/x')
        self.assertEqual(
            auth.scheme_host_port_prefix(scheme='https', host='z1', port=443),
            'https://z1')
        self.assertEqual(
            auth.scheme_host_port_prefix(scheme='https', host='z2', port=444),
            'https://z2:444')

    def test10_null_handlers(self):
        """Test null handlers."""
        self.assertEqual(IIIFAuth().access_token_handler, None)
        self.assertEqual(IIIFAuth().client_id_handler, None)
        self.assertEqual(IIIFAuth().home_handler, None)

    def test11_access_token_response(self):
        """Test structure of access token response."""
        # no token
        err_response = IIIFAuth().access_token_response(None)
        self.assertEqual(err_response['error'], 'client_unauthorized')
        self.assertFalse('access_token' in err_response)
        # token
        good_response = IIIFAuth().access_token_response('TOKEN_HERE')
        self.assertEqual(good_response['accessToken'], 'TOKEN_HERE')
        self.assertEqual(good_response['tokenType'], 'Bearer')
        self.assertTrue(int(good_response['expiresIn']) > 1000)
        self.assertFalse('error' in good_response)

    def test11_null_authn_authz(self):
        """Test null authn and auth.

        No auth so they return False always.
        """
        self.assertEqual(IIIFAuth().info_authn(), False)
        self.assertEqual(IIIFAuth().info_authz(), False)
        self.assertEqual(IIIFAuth().image_authn(), False)
        self.assertEqual(IIIFAuth().image_authz(), False)
