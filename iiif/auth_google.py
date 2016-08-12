"""IIIF Authentication via Google.

FIXME - this code assumes Flask webapp framework, should be abstracted
"""

import hashlib
import json
import re
import sys
import time
import os.path
try:
    # python3
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.parse import urlencode
except ImportError:
    # fall back to python2
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib import urlencode
from flask import request, make_response, redirect

from .auth import IIIFAuth


class IIIFAuthGoogle(IIIFAuth):
    """IIIF Authentication Class using Google Auth."""

    def __init__(self, client_secret_file='client_secret.json', cookie_prefix=None):
        """Initialize IIIFAuthGoogle object.

        Sets a number of constants and attempts to load client client_secret
        data from client_secret_file.
        """
        super(IIIFAuthGoogle, self).__init__(cookie_prefix=cookie_prefix)
        #
        try:
            # Assign defaults so code/tests will have some data even if load
            # fails
            self.google_api_scope = 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
            self.google_oauth2_url = 'https://accounts.google.com/o/oauth2/'
            self.google_api_url = 'https://www.googleapis.com/oauth2/v1/'
            self.google_api_client_id = 'oops_missing_client_id'
            self.google_api_client_secret = 'oops_missing_client_secret'
            gcd = json.loads(open(client_secret_file).read())
            self.google_api_client_id = gcd['web']['client_id']
            self.google_api_client_secret = gcd['web']['client_secret']
        except Exception as e:
            self.logger.error("Failed to load Google auth from %s: %s" % (
                client_secret_file, str(e)))
        #
        # Auth data
        self.tokens = {}
        #
        self.auth_type = 'Google auth'
        self.account_cookie_name = self.cookie_prefix + 'account'

    def info_authn(self):
        """Check to see if user if authenticated for info.json.

        Must have Authorization header with value that is an appropriate
        token.
        """
        authz_header = request.headers.get('Authorization', '[none]')
        return self.token_valid(authz_header, "info_authn: Authorization header")

    def image_authn(self):
        """Check to see if user if authenticated for image requests.

        Must have auth cookie with an appropriate token value.
        """
        authn_cookie = request.cookies.get(self.auth_cookie_name, default='[none]')
        return self.token_valid(authn_cookie, "image_authn: auth cookie")

    def token_valid(self, token, log_msg):
        """Check token validity.

        Returns true if the token is valid. The set of allowed tokens is
        stored in self.tokens.

        Uses log_msg as prefix to info level log message of accetance or
        rejection.
        """
        if (token in self.tokens):
            age = int(time.time()) - self.tokens[token]
            self.logger.info(log_msg + " " + token + " ACCEPTED (%ds old)" % age)
            return True
        else:
            self.logger.info(log_msg + " " + token + " REJECTED")
            return False  
      
    def login_handler(self, config=None, prefix=None, **args):
        """OAuth starts here. This will redirect User to Google."""
        params = {
            'response_type': 'code',
            'client_id': self.google_api_client_id,
            'redirect_uri': self.scheme_host_port_prefix('http', config.host, config.port, prefix) + '/home',
            'scope': self.google_api_scope,
            'state': request.args.get('next', default=''),
        }
        url = self.google_oauth2_url + 'auth?' + urlencode(params)
        response = redirect(url)
        response.headers['Access-control-allow-origin'] = '*'
        return response

    def logout_handler(self, **args):
        """Handler for logout button.

        Delete cookies and return HTML that immediately closes window
        """
        response = make_response(
            "<html><script>window.close();</script></html>", 200, {'Content-Type': "text/html"})
        response.set_cookie(self.account_cookie_name, expires=0)
        response.set_cookie(self.auth_cookie_name, expires=0)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    def access_token_handler(self, **args):
        """Get access token based on cookie sent with this request.

        This handler deals with two cases:

        1) Non-browser client (indicated by no messageId set in request)
        where the response is a simple JSON response.

        2) Browser client (indicate by messageId setin request) where
        the request must be made from a an iFrame and the response is 
        sent as JSON wrapped in HTML containing a postMessage() script
        that conveys the access token to the viewer.
        """
        message_id = request.args.get('messageId', default='')
        account = request.cookies.get(self.account_cookie_name, default='')
        token = self.access_token(account)
        data_str = json.dumps(self.access_token_response(token, message_id))

        ct = "application/json"
        if (message_id):
            data_str = """<html>
<body>
<p>postMessage ACCESS TOKEN %s</p>
<script>
(window.opener || window.parent).postMessage(%s, '*');    
</script>
</body>
</html>
""" % (token, data_str)
            ct = "text/html" # FIXME - does spec need to be explicit about content type?
        # Build response
        response = make_response(data_str, 200, {'Content-Type': ct})
        if (token):
            # Set the cookie for the image content
            self.logger.info("access_token_handler: sending token via cookie = " + token)
            response.set_cookie(self.auth_cookie_name, token)
        response.headers['Access-control-allow-origin'] = '*'
        return response

    def home_handler(self, config=None, prefix=None, **args):
        """Handler for /home redirect path after Google auth.

        OAuth ends up back here from Google. Set the account cookie
        and close window to trigger next step.
        """
        gresponse = self.google_get_token(config, prefix)
        gdata = self.google_get_data(config, gresponse)

        email = gdata.get('email', 'NO_EMAIL')
        name = gdata.get('name', 'NO_NAME')
        response = make_response(
            "<html><script>window.close();</script></html>", 200, {'Content-Type': "text/html"})
        # FIXME - Identity probably should not be in the clear...
        response.set_cookie(self.account_cookie_name,
                            'Authenticated identity: ' + name + ' ' + email)
        return response

    def account_allowed(self, account):
        """True if the account credentials should be accepted.

        Default implementation is that any account is allowed,
        so response is True if account is True.
        """
        return True if (account) else False

    def access_token(self, account):
        """Make and store access token from account data.

        If account is set then make a token and add it to the dict
        of accepted tokens with current timestamp as the value. Return
        the token.

        Otherwise return None.

        FIXME - This should be secure! For now just make a trivial 
        hash.
        """
        if (self.account_allowed(account)):
            token = hashlib.sha1(("SeCrEt StUFF 'ERe" + account).encode('utf-8')).hexdigest()
            self.tokens[token] = int(time.time())
            return token
        else:
            return None

    ######################################################################
    # Code to get data from Google API
    #

    def google_get_token(self, config, prefix):
        """Make request to Google API to get token."""
        params = {
            'code': request.args.get('code', default=''),
            'client_id': self.google_api_client_id,
            'client_secret': self.google_api_client_secret,
            'redirect_uri': self.scheme_host_port_prefix('http', config.host, config.port, prefix) + '/home',
            'grant_type': 'authorization_code',
        }
        payload = urlencode(params).encode('utf-8')
        url = self.google_oauth2_url + 'token'
        req = Request(url, payload)
        json_str = urlopen(req).read()
        if sys.version_info < (3, 0): #FIXME - is there a cleaner way to handle py2/3?
            json_str = json_str.decode('utf-8')
        return json.loads(json_str)

    def google_get_data(self, config, response):
        """Make request to Google API to get profile data for the user."""
        params = {
            'access_token': response['access_token'],
        }
        payload = urlencode(params)
        url = self.google_api_url + 'userinfo?' + payload
        req = Request(url)
        json_str = urlopen(req).read()
        if sys.version_info < (3, 0): #FIXME - is there a cleaner way to handle py2/3?
            json_str = json_str.decode('utf-8')
        return json.loads(json_str)
