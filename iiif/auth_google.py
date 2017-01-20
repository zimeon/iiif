"""IIIF Authentication using the login interaction pattern via Google.

See <http://iiif.io/api/auth/#login-interaction-pattern>.
This code is specifc to the Flask webapp framework.
"""

import json
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

from .auth_flask import IIIFAuthFlask


class IIIFAuthGoogle(IIIFAuthFlask):
    """IIIF Authentication Class using Google Auth."""

    def __init__(self, client_secret_file='client_secret.json',
                 cookie_prefix=None):
        """Initialize IIIFAuthGoogle object.

        Sets a number of constants and attempts to load client client_secret
        data from client_secret_file.
        """
        super(IIIFAuthGoogle, self).__init__(cookie_prefix=cookie_prefix)
        #
        self.auth_pattern = 'login'
        self.auth_type = 'Google auth'
        try:
            # Assign defaults so code/tests will have some data even if load
            # fails
            self.google_api_scope = (  # pep8 long string...
                'https://www.googleapis.com/auth/userinfo.profile '
                'https://www.googleapis.com/auth/userinfo.email')
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

    def login_handler(self, config=None, prefix=None, **args):
        """OAuth starts here, redirect user to Google."""
        params = {
            'response_type': 'code',
            'client_id': self.google_api_client_id,
            'redirect_uri': self.scheme_host_port_prefix(
                'http', config.host, config.port, prefix) + '/home',
            'scope': self.google_api_scope,
            'state': self.request_args_get('next', default=''),
        }
        url = self.google_oauth2_url + 'auth?' + urlencode(params)
        return self.login_handler_redirect(url)

    def home_handler(self, config=None, prefix=None, **args):
        """Handler for /home redirect path after Google auth.

        OAuth ends up back here from Google. Set the account cookie
        and close window to trigger next step.
        """
        gresponse = self.google_get_token(config, prefix)
        gdata = self.google_get_data(config, gresponse)
        email = gdata.get('email', 'NO_EMAIL')
        name = gdata.get('name', 'NO_NAME')
        # Make and store cookie from identity, set and close window
        cookie = self.access_cookie(name + ' ' + email)
        return self.set_cookie_close_window_response(cookie)

    ######################################################################
    # Code to get data from Google API
    #

    def google_get_token(self, config, prefix):
        """Make request to Google API to get token."""
        params = {
            'code': self.request_args_get(
                'code',
                default=''),
            'client_id': self.google_api_client_id,
            'client_secret': self.google_api_client_secret,
            'redirect_uri': self.scheme_host_port_prefix(
                'http', config.host, config.port, prefix) + '/home',
            'grant_type': 'authorization_code',
        }
        payload = urlencode(params).encode('utf-8')
        url = self.google_oauth2_url + 'token'
        req = Request(url, payload)
        json_str = urlopen(req).read()
        return json.loads(json_str.decode('utf-8'))

    def google_get_data(self, config, response):
        """Make request to Google API to get profile data for the user."""
        params = {
            'access_token': response['access_token'],
        }
        payload = urlencode(params)
        url = self.google_api_url + 'userinfo?' + payload
        req = Request(url)
        json_str = urlopen(req).read()
        return json.loads(json_str.decode('utf-8'))
