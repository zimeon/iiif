"""IIIF Authentication for a simple clickthrough.

Trivial code to immediately close the login window and
set the account cookie.
"""

from .auth_flask import IIIFAuthFlask


class IIIFAuthClickthrough(IIIFAuthFlask):
    """IIIF Authentication class using a simple clickthrough."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthBasic object."""
        super(IIIFAuthClickthrough, self).__init__(cookie_prefix=cookie_prefix)
        self.auth_type = 'clickthrough'

    def login_handler(self, config=None, prefix=None, **args):
        """Login handler for clickthrough.

        We simply set the account cooke and close the login
        window, there is not authentication per se.
        """
        return self.set_cookie_close_window_response("clickthrough-ok")

    # No logout for clickthrough
    logout_handler = None
