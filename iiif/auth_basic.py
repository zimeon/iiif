"""IIIF Authentication using HTTP Basic auth.

See <http://iiif.io/api/auth/#login-interaction-pattern>.

This code extends IIIFAuthFlask and is thus specific to the
Flask framework.
"""

import json
import re
import os.path
from flask import request, make_response

from .auth_flask import IIIFAuthFlask


class IIIFAuthBasic(IIIFAuthFlask):
    """IIIF Authentication Class using HTTP Basic Auth."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthBasic object."""
        super(IIIFAuthBasic, self).__init__(cookie_prefix=cookie_prefix)
        self.auth_pattern = 'login'
        self.auth_type = 'basic auth'

    def login_handler(self, config=None, prefix=None, **args):
        """HTTP Basic login handler.

        Respond with 401 and WWW-Authenticate header if there are no
        credentials or bad credentials. If there are credentials then
        simply check for username equal to password for validity.
        """
        headers = {}
        headers['Access-control-allow-origin'] = '*'
        headers['Content-type'] = 'text/html'
        auth = request.authorization
        if (auth and auth.username == auth.password):
            return self.set_cookie_close_window_response(
                "valid-http-basic-login")
        else:
            headers['WWW-Authenticate'] = (
                'Basic realm="HTTP-Basic-Auth at %s (u=p to login)"' %
                (self.name))
            return make_response("", 401, headers)
