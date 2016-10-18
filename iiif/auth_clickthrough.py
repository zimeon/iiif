"""IIIF Authentication for the clickthrough interaction pattern.

See <http://iiif.io/api/auth/#clickthrough-interaction-pattern>.
Trivial code to immediately close the login window and
set the account cookie.
"""

from .auth_flask import IIIFAuthFlask


class IIIFAuthClickthrough(IIIFAuthFlask):
    """IIIF Authentication class using a simple clickthrough."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthBasic object."""
        super(IIIFAuthClickthrough, self).__init__(cookie_prefix=cookie_prefix)
        self.auth_pattern = 'clickthrough'
        self.header = 'Restricted Material with Terms of Use'
        self.description = 'Use on condition of saying "IIIF is great!"'
        self.confirm_label = 'I agree'

    def login_service_description(self):
        """Clickthrough login service description.

        The login service description _MUST_ include the token service
        description. Additionally, for a clickthroudh loginThe authentication pattern is indicated via the
        profile URI which is built using self.auth_pattern.
        """
        desc = super(IIIFAuthClickthrough, self).login_service_description()
        desc['confirmLabel'] = self.confirm_label
        return desc

    def login_handler(self, config=None, prefix=None, **args):
        """Login handler for clickthrough.

        We simply set the account cooke and close the login
        window, there is not authentication per se.
        """
        return self.set_cookie_close_window_response("clickthrough-ok")

    # No logout for clickthrough
    logout_handler = None
