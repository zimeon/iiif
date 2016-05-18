"""IIIF Authentication via Google.

FIXME - this code assumes Flask webapp framework, should be abstracted
"""

import json
import re
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
        self.account_cookie_name = self.cookie_prefix + 'account'

    def info_authn(self):
        """Check to see if user if authenticated for info.json.

        Must have Authorization header with value that is the appropriate
        token.
        """
        self.logger.info("info_authn: Authorization header = " +
                         request.headers.get('Authorization', '[none]'))
        return(request.headers.get('Authorization', '') != '')

    def image_authn(self):
        """Check to see if user if authenticated for image requests.

        Must have auth cookie with known token value.
        """
        self.logger.info("image_authn: auth cookie = " +
                         request.cookies.get(self.auth_cookie_name, default='[none]'))
        return request.cookies.get(self.auth_cookie_name, default='')

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

        The client requests a token to send in re-request for info.json.
        Support JSONP request to get the token to send to info.json in
        Auth'z header.
        """
        callback_function = request.args.get('callback', default='')
        authcode = request.args.get('code', default='')
        account = request.cookies.get(self.account_cookie_name, default='')
        if (account):
            data = {"access_token": account,
                    "token_type": "Bearer", "expires_in": 3600}
        else:
            data = {"error": "client_unauthorized",
                    "error_description": "No login details received"}
        data_str = json.dumps(data)

        ct = "application/json"
        if (callback_function):
            data_str = "%s(%s);" % (callback_function, data_str)
            ct = "application/javascript"
        # Build response
        response = make_response(data_str, 200, {'Content-Type': ct})
        if (account):
            # Set the cookie for the image content -- FIXME - need something
            # real
            response.set_cookie(self.auth_cookie_name, account)
        response.headers['Access-control-allow-origin'] = '*'
        return response

    def home_handler(self, config=None, prefix=None, **args):
        """Handler for /home redirect path after Goole auth.

        OAuth ends up back here from Google. Set the account cookie
        and close window to trigger next step.
        """
        gresponse = self.google_get_token(config, prefix)
        gdata = self.google_get_data(config, gresponse)

        email = gdata.get('email', 'NO_EMAIL')
        name = gdata.get('name', 'NO_NAME')
        response = make_response(
            "<html><script>window.close();</script></html>", 200, {'Content-Type': "text/html"})
        response.set_cookie(self.account_cookie_name,
                            'Token for ' + name + ' ' + email)
        return response

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
        return json.loads(urlopen(req).read())

    def google_get_data(self, config, response):
        """Make request to Google API to get profile data for the user."""
        params = {
            'access_token': response['access_token'],
        }
        payload = urlencode(params)
        url = self.google_api_url + 'userinfo?' + payload
        req = Request(url)
        return json.loads(urlopen(req).read())
