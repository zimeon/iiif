"""IIIF Authentication for a Flask application.

Extends iiif.auth to add Flask web application interaction
necessary to build a real auth system. In theory one
might be able to replace this module as the middle
component to work with another framework.
"""

import json
from flask import request, make_response, redirect

from .auth import IIIFAuth


class IIIFAuthFlask(IIIFAuth):
    """IIIF Authentication Class for a Flask application."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthFlask object."""
        super(IIIFAuthFlask, self).__init__(cookie_prefix=cookie_prefix)
        self.account_cookie_name = self.cookie_prefix + 'account'

    def info_authn(self):
        """Check to see if user if authenticated for info.json.

        Must have Authorization header with value that has the form
        "Bearer TOKEN", where TOKEN is an appropriate and valid access
        token.
        """
        authz_header = request.headers.get('Authorization', '[none]')
        if (not authz_header.startswith('Bearer ')):
            return False
        token = authz_header[7:]
        return self.access_token_valid(
            token, "info_authn: Authorization header")

    def image_authn(self):
        """Check to see if user if authenticated for image requests.

        Must have access cookie with an appropriate value.
        """
        authn_cookie = request.cookies.get(
            self.access_cookie_name, default='[none]')
        return self.access_cookie_valid(authn_cookie, "image_authn: auth cookie")

    def login_handler_redirect(self, url):
        """Complete login handler behavior with redirect.

        There will be some authentication specific code before but
        it will return the value from this method which builds the
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
        response.set_cookie(self.access_cookie_name, expires=0)
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
        message_id = request.args.get('messageId', default=None)
        origin = request.args.get('origin', default='unknown_origin')
        self.logger.info("access_token_handler: origin = " + origin)
        account = request.cookies.get(self.account_cookie_name, default='')
        token = self.access_token(account)

        # Build JSON response
        data_str = json.dumps(self.access_token_response(token, message_id))
        ct = "application/json"

        # If message_id is set the wrap in HTML with postMessage JavaScript
        # for a browser client
        if (message_id is not None):
            data_str = """<html>
<body style="margin: 0px;">
<div>postMessage ACCESS TOKEN %s</div>
<script>
window.parent.postMessage(%s, '%s');
</script>
</body>
</html>
""" % (token, data_str, origin)
            ct = "text/html"

        # Send response along with cookie
        response = make_response(data_str, 200, {'Content-Type': ct})
        if (token):
            self.logger.info(
                "access_token_handler: setting access token = " + token)
            # Set the cookie for the image content
            cookie = self.access_cookie(token)
            self.logger.info(
                "access_token_handler: setting access cookie = " + cookie)
            response.set_cookie(self.access_cookie_name, cookie)
        else:
            self.logger.info(
                "access_token_handler: auth failed, sending error")
        response.headers['Access-control-allow-origin'] = '*'
        return response

    def set_cookie_close_window_response(self, account_cookie_value):
        """Response to set account cookie and close window HTML/JavaScript."""
        response = make_response(
            "<html><script>window.close();</script></html>", 200,
            {'Content-Type': "text/html"})
        response.set_cookie(self.account_cookie_name,
                            account_cookie_value)
        return response

    def request_args_get(self, name, default=''):
        """Wrapper for request.args.get()."""
        return request.args.get(name, default)
