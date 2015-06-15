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

    def logout_service_description(self):
        """Logout service description with has modified URI to supply 'bad' credentials

        With HTTP Basic auth there are no clean ways to logout (except browser specific
        extensions). The standard recommendation seems to be to supply bad credentials.
        which we do in the URI (bad@X).
        """
        uri = re.sub(r'''^https?://''', lambda m: m.group(0)+'bad:X@' , self.logout_uri)
        return( { "@id": uri,
                  "profile": self.profile_base+'logout',
                  "label": 'Logout from '+self.name
                } )

    def info_authn(self):
        """Check to see if user if authenticated for info.json"""
        print "info_authz: Authorization header = " + request.headers.get('Authorization', '[none]')
        return (request.headers.get('Authorization', '') != '') #FIXME - check valaue

    def image_authn(self):
        """Check to see if user if authenticated for image requets"""
        print "image_authn: loggedin cookie = " + request.cookies.get("basic_token",default='[none]')
        return request.cookies.get("basic_token",default='') #FIXME - check value

    def login_handler(self, config=None, prefix=None, **args):
        """HTTP Basic login handler

        Respond with 401 and WWW-Authenticate header if there are no credentials
        or bad credentials. If there are credentials then simply check for username
        equal to password for validity. 
        """
        headers = {}
        headers['Access-control-allow-origin']='*'
        headers['Content-type']='text/html'
        auth = request.authorization
        if (auth and auth.username == auth.password):
            html = "<html><script>window.close();</script></html>"
            response = make_response(html,200,headers)
            response.set_cookie("basic_authdone", "valid-http-basic-login", expires=3600)
            return response
        else:
            headers['WWW-Authenticate']='Basic realm="HTTP-Basic-Auth at %s (u=p to login)"' % (self.name)
            return make_response("",401,headers)
 
    def logout_handler(self, **args):
        """Handler for logout button

        Delete cookies and return HTML that immediately closes window. Logout
        is tricky but attempt to do this via self.logout_uri which as has
        bad username:password.
        """
        response = make_response("<html><script>window.close();</script></html>", 200, {'Content-Type':"text/html"});
        response.set_cookie("basic_authdone", expires=0)
        response.set_cookie("basic_token", expires=0)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    def access_token_handler(self, **args):
        # This is the next step -- client requests a token to send to info.json
        # We're going to just copy it from our cookie.
        # JSONP request to get the token to send to info.json in Auth'z header
        callback_function = request.args.get('callback',default='')
        authdone = request.headers.get('Authorization', '')
        if (authdone):
            token = 'secret_token_here' # FIXME - need something real
            data = {"access_token": token, "token_type": "Bearer", "expires_in": 3600}
        else:
            data = {"error":"client_unauthorized","error_description": "No login details received"}
        data_str = json.dumps(data)

        ct = "application/json"
        if (callback_function):
            data_str = "%s(%s);" % (callback_function, data_str)
            ct = "application/javascript"
        # Build response
        response = make_response(data_str,200,{'Content-Type':ct})
        if (authdone):
            # Set the cookie for the image content -- FIXME - need something real
            response.set_cookie('basic_token', token)
        response.headers['Access-control-allow-origin']='*'
        return response 