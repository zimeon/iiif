"""IIIF Authentication for the external interaction pattern.

See <http://iiif.io/api/auth/#external-interaction-pattern>.
Trivial code to immediately close the login window and
set the account cookie.
"""

from .auth_flask import IIIFAuthFlask


class IIIFAuthExternal(IIIFAuthFlask):
    """IIIF Authentication class using a simple external."""

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuthBasic object."""
        super(IIIFAuthExternal, self).__init__(cookie_prefix=cookie_prefix)
        self.auth_pattern = 'external'
        self.label = 'External Authentication Required'
        self.failureHeader = 'Restricted Material'
        self.failureDescription = 'This material is not viewable without prior agreement'

    def login_service_description(self):
        """External login service description.

        The login service description _MUST_ include the token service
        description. For the external interaction pattern we have
        a dummy URI for the access cookie service.
        """
        desc = super(IIIFAuthExternal, self).login_service_description()
        return desc

    def login_handler(self, config=None, prefix=None, **args):
        """Null login handler for external.

        We provide no support for getting the access cookie,
        this must be done by the use via some out-of-band means.
        """
        return True

    # No logout for external
    logout_handler = None
