"""Test code for iiif.auth"""
import json
import re
import unittest

from iiif.auth import IIIFAuth
from iiif.info import IIIFInfo

class TestAll(unittest.TestCase):

    def test01_init(self):
        auth = IIIFAuth()
        self.assertEqual( auth.profile_base, 'http://iiif.io/api/image/2/auth/' )
        self.assertEqual( auth.name, "image server" )
        auth = IIIFAuth(cookie_prefix='abc_')
        self.assertEqual( auth.cookie_prefix, 'abc_' )
        self.assertEqual( auth.auth_cookie_name, 'abc_loggedin' )
        self.assertEqual( auth.token_cookie_name, 'abc_token' )

    def test02_set_cookie_prefix(self):
        auth = IIIFAuth()
        self.assertTrue( re.match(r'\d{6}_$',auth.cookie_prefix) )
        auth.set_cookie_prefix()
        self.assertTrue( re.match(r'\d{6}_$',auth.cookie_prefix) )
        auth.set_cookie_prefix('ghi')
        self.assertEqual( auth.cookie_prefix, 'ghi' )

    def test03_add_services(self):

        info = IIIFInfo()
        auth = IIIFAuth()
        self.assertEqual( info.service, None )
        # first just login
        auth.add_services(info)
        self.assertEqual( info.service, None )
        auth.login_uri = 'Xlogin'
        auth.add_services(info)
        self.assertEqual( info.service['@id'], 'Xlogin' )
        # then just logout
        info = IIIFInfo()
        auth = IIIFAuth()
        auth.logout_uri = 'Ylogout'
        auth.add_services(info)
        self.assertEqual( info.service['@id'], 'Ylogout' )
        # now add all, check we have all @ids in service description
        info = IIIFInfo()
        auth = IIIFAuth()
        auth.login_uri = 'Zlogin'
        auth.logout_uri = 'Zlogout'
        auth.client_id_uri = 'Zclient'
        auth.access_token_uri = 'Ztoken'
        auth.add_services(info)
        self.assertEqual( len(info.service), 4 )
        ids = set([ e['@id'] for e in info.service ])
        self.assertEqual( ids, set([auth.login_uri,auth.logout_uri,auth.client_id_uri,auth.access_token_uri]) )

    def test04_login_service_description(self):
        auth = IIIFAuth()
        lsd = auth.login_service_description()
        self.assertEqual( lsd['profile'], 'http://iiif.io/api/image/2/auth/login' )
        auth.login_uri = 'id1'
        auth.profile_base = 'http://pb1/'
        lsd = auth.login_service_description()
        self.assertEqual( lsd['@id'], 'id1' )
        self.assertEqual( lsd['profile'], 'http://pb1/login' )

    def test05_logout_service_description(self):
        auth = IIIFAuth()
        auth.logout_uri = 'id2'
        auth.profile_base = 'http://pb2/'
        lsd = auth.logout_service_description()
        self.assertEqual( lsd['@id'], 'id2' )
        self.assertEqual( lsd['profile'], 'http://pb2/logout' )

    def test06_client_id_service_description(self):
        auth = IIIFAuth()
        auth.client_id_uri = 'id3'
        auth.profile_base = 'http://pb3/'
        lsd = auth.client_id_service_description()
        self.assertEqual( lsd['@id'], 'id3' )
        self.assertEqual( lsd['profile'], 'http://pb3/clientId' )

    def test07_access_token_service_description(self):
        auth = IIIFAuth()
        auth.access_token_uri = 'id4'
        auth.profile_base = 'http://pb4/'
        lsd = auth.access_token_service_description()
        self.assertEqual( lsd['@id'], 'id4' )
        self.assertEqual( lsd['profile'], 'http://pb4/token' )

    def test08_access_token_response(self):
        #, query, cookies):
        pass

    def test09_host_port_prefix(self):
        auth = IIIFAuth()
        self.assertEqual( auth.scheme_host_port_prefix('sc','x', '9', 'z'), 'sc://x:9/z' )
        self.assertEqual( auth.scheme_host_port_prefix(host='x', prefix='z'), 'http://x/z' )
        self.assertEqual( auth.scheme_host_port_prefix(host='yy'), 'http://yy' )
        self.assertEqual( auth.scheme_host_port_prefix(host='yy',port=80), 'http://yy' )
        self.assertEqual( auth.scheme_host_port_prefix(host='yy',port=81,prefix='x'), 'http://yy:81/x' )
        self.assertEqual( auth.scheme_host_port_prefix(scheme='https',host='z1',port=443), 'https://z1' )
        self.assertEqual( auth.scheme_host_port_prefix(scheme='https',host='z2',port=444), 'https://z2:444' )

    def test10_client_id_handler(self):
        self.assertEqual( IIIFAuth().client_id_handler, None )

    def test11_home_handler(self):
        self.assertEqual( IIIFAuth().home_handler, None )

    def test12_info_authn(self): 
        self.assertEqual( IIIFAuth().info_authn(), False )

    def test13_info_authz(self): 
        self.assertEqual( IIIFAuth().info_authz(), False )

    def test14_image_authn(self): 
        self.assertEqual( IIIFAuth().image_authn(), False )

    def test15_image_authz(self): 
        self.assertEqual( IIIFAuth().image_authz(), False )
