"""IIIF Authentication for the kiosk interaction pattern.

See <http://iiif.io/api/auth/#kiosk-interaction-pattern>.
Trivial code to immediately close the login window and
set the account cookie.
"""

from .auth_flask import IIIFAuthFlask


class IIIFAuthKiosk(IIIFAuthFlask):
    """IIIF Authentication class with no user interaction."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthBasic object."""
        super(IIIFAuthKiosk, self).__init__(cookie_prefix=cookie_prefix)
        self.auth_pattern = 'kiosk'
        self.header = 'Kiosk setup in progress, please wait...'

    def login_handler(self, config=None, prefix=None, **args):
        """Login handler for kiosk.

        Override this method to do any checks to do kiosk auth, e.g. we might
        test the orginator of the request or similar. In this null
        implementation we simply set the account cookie and close the login
        window, there is no authentication per se.
        """
        return self.set_cookie_close_window_response("kiosk-null-ok")

    # No logout for kiosk pattern
    logout_handler = None
