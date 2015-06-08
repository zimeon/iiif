"""IIIF Authentication using HTTP Basic auth

FIXME - this code assumes Flask webapp framework, should be abstracted
"""

import json
import re
import os.path
import urllib
import urllib2
from flask import request, make_response, redirect

from iiif.auth import IIIFAuth

class IIIFAuthBasic(IIIFAuth):

    def __init__(self, homedir):
        super(IIIFAuthBasic, self).__init__()

    def is_authn(self):
        """Check to see if user if authenticated"""
        print "is_authn: loggedin cookie = " + request.cookies.get("loggedin",default='[none]')
        return request.cookies.get("loggedin",default='')

    def is_authz(self): 
        """Check to see if user if authenticated and authorized"""
        # FIXME - need to check contents of this jeadr
        #
        #return (is_authn() and request.headers.get('Authorization', '') != '')
        print "is_authz: Authorization header = " + request.headers.get('Authorization', '[none]')
        return (request.headers.get('Authorization', '') != '')

    def login_handler(self, config=None, prefix=None, **args):
        """OAuth starts here. This will redirect User to Google"""
        params = {
            'response_type': 'code',
            'client_id': self.google_api_client_id,
            'redirect_uri': self.host_port_prefix(config.host,config.port,prefix)+'/home',
            'scope': self.google_api_scope,
            'state': request.args.get('next',default=''),
        }
        url = self.google_oauth2_url + 'auth?' + urllib.urlencode(params)
        response = redirect(url)
        response.headers['Access-control-allow-origin']='*'
        return response 

    def logout_handler(self, **args):
        """Handler for logout button

        Delete cookies and return HTML that immediately closes window
        """
        response = make_response("<html><script>window.close();</script></html>", 200, {'Content-Type':"text/html"});
        response.set_cookie("account", expires=0)
        response.set_cookie("loggedin", expires=0)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    def access_token_handler(self, **args):
        # This is the next step -- client requests a token to send to info.json
        # We're going to just copy it from our cookie.
        # JSONP request to get the token to send to info.json in Auth'z header
        callback_function = request.args.get('callback',default='')
        authcode = request.args.get('code',default='')
        account = request.cookies.get('account',default='')
        if (account):
            data = {"access_token":account, "token_type": "Bearer", "expires_in": 3600}
        else:
            data = {"error":"client_unauthorized","error_description": "No login details received"}
        data_str = json.dumps(data)

        ct = "application/json"
        if (callback_function):
            data_str = "%s(%s);" % (callback_function, data_str)
            ct = "application/javascript"
        # Build response
        response = make_response(data_str,200,{'Content-Type':ct})
        if (account):
            # Set the cookie for the image content -- FIXME - need something real
            response.set_cookie('loggedin', account)
        response.set_cookie('account', expires=0)
        response.headers['Access-control-allow-origin']='*'
        return response 

    def home_handler(self, config=None, prefix=None, **args):
        """Handler for /home redirect path after Goole auth

        OAuth ends up back here from Google. Set the account cookie 
        and close window to trigger next step
        """
        gresponse = self.google_get_token(config, prefix)
        gdata = self.google_get_data(config, gresponse)

        email = gdata.get('email', 'NO_EMAIL')
        name = gdata.get('name', 'NO_NAME')
        response = make_response("<html><script>window.close();</script></html>", 200, {'Content-Type':"text/html"});
        response.set_cookie("account", 'Token for '+name+' '+email)
        return response

    ######################################################################
    # Code to get data from Google API
    #

    def google_get_token(self, config, prefix):
        # Google OAuth2 helpers
        params = {
            'code': request.args.get('code',default=''),
            'client_id': self.google_api_client_id,
            'client_secret': self.google_api_client_secret,
            'redirect_uri': self.host_port_prefix(config.host,config.port,prefix)+'/home',
            'grant_type': 'authorization_code',
        }
        payload = urllib.urlencode(params)
        url = self.google_oauth2_url + 'token'
        req = urllib2.Request(url, payload) 
        return json.loads(urllib2.urlopen(req).read())

    def google_get_data(self, config, response):
        """Make request to Google API to get profile data for the user"""
        params = {
            'access_token': response['access_token'],
        }
        payload = urllib.urlencode(params)
        url = self.google_api_url + 'userinfo?' + payload
        req = urllib2.Request(url)  # must be GET
        return json.loads(urllib2.urlopen(req).read())
