"""IIIF Authentication for a Flask application.

Extends iiif.auth to add Flask web application interaction
necessary to build a real auth system. In theory one
might be able to replace this module as the middle
component.
"""

import hashlib
import json
import time
from flask import request, make_response, redirect

from .auth import IIIFAuth


class IIIFAuthFlask(IIIFAuth):
    """IIIF Authentication Class for a Flask application."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthFlask object."""
        super(IIIFAuthFlask, self).__init__(cookie_prefix=cookie_prefix)

    def info_authn(self):
        """Check to see if user if authenticated for info.json.

        Must have Authorization header with value that is an appropriate
        token.
        """
        authz_header = request.headers.get('Authorization', '[none]')
        return self.token_valid(
            authz_header, "info_authn: Authorization header")

    def image_authn(self):
        """Check to see if user if authenticated for image requests.

        Must have auth cookie with an appropriate token value.
        """
        authn_cookie = request.cookies.get(
            self.auth_cookie_name, default='[none]')
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
            self.logger.info(log_msg + " " + token +
                             " ACCEPTED (%ds old)" % age)
            return True
        else:
            self.logger.info(log_msg + " " + token + " REJECTED")
            return False

    def login_handler_redirect(self, url):
        """Complete login handler behavior with redirect.

        There will be some authentication specific code before but
        it will return the value fro this method which builds the
        Flask redirect response.
        """
        response = redirect(url)
        response.headers['Access-control-allow-origin'] = '*'
        return response

    def logout_handler(self, **args):
        """Handler for logout button.

        Delete cookies and return HTML that immediately closes window
        """
        response = make_response(
            "<html><script>window.close();</script></html>", 200,
            {'Content-Type': "text/html"})
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
<body style="margin: 0px;">
<div>postMessage ACCESS TOKEN %s</div>
<script>
(window.opener || window.parent).postMessage(%s, '*');
</script>
</body>
</html>
""" % (token, data_str)
            ct = "text/html"
        # Build response
        response = make_response(data_str, 200, {'Content-Type': ct})
        if (token):
            # Set the cookie for the image content
            self.logger.info(
                "access_token_handler: sending token via cookie = " + token)
            response.set_cookie(self.auth_cookie_name, token)
        response.headers['Access-control-allow-origin'] = '*'
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
            token = hashlib.sha1(
                ("SeCrEt StUFF 'ERe" + account).encode('utf-8')).hexdigest()
            self.tokens[token] = int(time.time())
            return token
        else:
            return None

    def set_cookie_close_window_response(self, account_cookie_value):
        """Response with cookie set and close window HTML/JavaScript."""
        response = make_response(
            "<html><script>window.close();</script></html>", 200,
            {'Content-Type': "text/html"})
        response.set_cookie(self.account_cookie_name,
                            account_cookie_value)
        return response

    def request_args_get(self, name, default=''):
        """Wrapper for request.args.get()."""
        return request.args.get(name, default)
