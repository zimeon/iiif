"""Support for IIIF Authentication."""

import json
import logging
import random
import re
import string
import time


class IIIFAuth(object):
    """IIIF Authentication Class.

    Base authentication class which does not actually implement an
    authentication scheme but is a foundation for specific sub-classes
    for different schemes.
    """

    def __init__(self, cookie_prefix=None):
        """Initialize IIIFAuth object."""
        self.profile_base = 'http://iiif.io/api/auth/1/'
        self.name = 'image server'
        self.auth_pattern = 'login'
        self.header = None
        self.description = None
        self.auth_type = None
        self.login_uri = None
        self.logout_uri = None
        self.client_id_uri = None
        self.access_token_uri = None
        self.logger = logging.getLogger(__name__)
        # Need to have different cookie names for each auth domain
        # running on the same server
        self.set_cookie_prefix(cookie_prefix)
        self.access_cookie_name = self.cookie_prefix + 'access'
        self.access_cookies = {}
        self.access_cookie_lifetime = 36000  # seconds
        self.access_tokens = {}
        self.access_token_lifetime = 600  # seconds

    def set_cookie_prefix(self, cookie_prefix=None):
        """Set a random cookie prefix unless one is specified.

        In order to run multiple demonstration auth services on the
        same server we need to have different cookie names for each
        auth domain. Unless cookie_prefix is set, generate a random
        one.
        """
        if (cookie_prefix is None):
            self.cookie_prefix = "%06d_" % int(random.random() * 1000000)
        else:
            self.cookie_prefix = cookie_prefix

    def add_services(self, info):
        """Add auth service descriptions to an IIIFInfo object.

        Login service description is the wrapper for all other
        auth service descriptions so we have nothing unless
        self.login_uri is specified. If we do then add any other
        auth services at children.

        Exactly the same structure is used in the authorized
        and unauthorized cases (although in the data could be
        different).
        """
        if (self.login_uri):
            svc = self.login_service_description()
            svcs = []
            if (self.logout_uri):
                svcs.append(self.logout_service_description())
            if (self.client_id_uri):
                svcs.append(self.client_id_service_description())
            if (self.access_token_uri):
                svcs.append(self.access_token_service_description())
            # Add one as direct child of service property, else array for >1
            if (len(svcs) == 1):
                svc['service'] = svcs[0]
            elif (len(svcs) > 1):
                svc['service'] = svcs
            info.add_service(svc)

    def login_service_description(self):
        """Login service description.

        The login service description _MUST_ include the token service
        description. The authentication pattern is indicated via the
        profile URI which is built using self.auth_pattern.
        """
        label = 'Login to ' + self.name
        if (self.auth_type):
            label = label + ' (' + self.auth_type + ')'
        desc = {"@id": self.login_uri,
                "profile": self.profile_base + self.auth_pattern,
                "label": label}
        if (self.header):
            desc['header'] = self.header
        if (self.description):
            desc['description'] = self.description
        return desc

    def logout_service_description(self):
        """Logout service description."""
        label = 'Logout from ' + self.name
        if (self.auth_type):
            label = label + ' (' + self.auth_type + ')'
        return({"@id": self.logout_uri,
                "profile": self.profile_base + 'logout',
                "label": label})

    def client_id_service_description(self):
        """Client Id service description."""
        return({"@id": self.client_id_uri,
                "profile": self.profile_base + 'clientId'})

    def access_token_service_description(self):
        """Access Token service description."""
        return({"@id": self.access_token_uri,
                "profile": self.profile_base + 'token'})

    # Override with method to implement
    access_token_handler = None

    def access_token_response(self, token, message_id=None):
        """Access token response structure.

        Success if token is set, otherwise (None, empty string) give error
        response. If message_id is set then an extra messageId attribute is
        set in the response to handle postMessage() responses.
        """
        if (token):
            data = {"accessToken": token,
                    "expiresIn": self.access_token_lifetime}
            if (message_id):
                data['messageId'] = message_id
        else:
            data = {"error": "client_unauthorized",
                    "description": "No authorization details received"}
        return data

    # Override with method to implement
    client_id_handler = None

    # Override with method to implement
    home_handler = None

    def info_authn(self):
        """Check to see if user is authenticated for info.json.

        Null implementation that always returns False, must override
        to implement authorization.
        """
        return False

    def info_authz(self):
        """Check to see if user is authenticated and authorized for info.json.

        Null implementation that says that any authenticated user is
        authorized.
        """
        return self.info_authn()

    def image_authn(self):
        """Check to see if user is authenticated for image requests.

        Null implementation that always returns False, must override
        to implement authorization.
        """
        return False

    def image_authz(self):
        """Check to see if user is authenticated and authorized for image requests.

        Null implementation that says that any authenticated user is
        authorized.
        """
        return self.image_authn()

    def scheme_host_port_prefix(self, scheme='http', host='host',
                                port=None, prefix=None):
        """Return URI composed of scheme, server, port, and prefix."""
        uri = scheme + '://' + host
        if (port and not ((scheme == 'http' and port == 80) or
                          (scheme == 'https' and port == 443))):
            uri += ':' + str(port)
        if (prefix):
            uri += '/' + prefix
        return uri

    def _generate_random_string(self, container, length=20):
        """Generate a random cookie or token string not in container.

        The cookie or token should be secure in the sense that it should not
        be likely to be able guess a value. Because it is not derived from
        anything else, there is no vulnerability of the token from computation,
        or possible leakage of information from the token.
        """
        while True:
            s = ''.join([random.SystemRandom().choice(string.digits + string.ascii_letters)
                         for n in range(length)])
            if (s not in container):
                break
        return s

    def account_allowed(self, account):
        """True if the account credentials should be accepted.

        Default implementation is that any account is allowed,
        so response is True if account is True. Override this method
        to authorize particular values of account.
        """
        return True if (account) else False

    def access_cookie(self, account):
        """Make and store access cookie for a given account.

        If account is allowed then make a cookie and add it to the dict
        of accepted access cookies with current timestamp as the value.
        Return the access cookie.

        Otherwise return None.
        """
        if (self.account_allowed(account)):
            cookie = self._generate_random_string(self.access_cookies)
            self.access_cookies[cookie] = int(time.time())
            return cookie
        else:
            return None

    def access_cookie_valid(self, cookie, log_msg):
        """Check access cookie validity.

        Returns true if the access cookie is valid. The set of allowed
        access cookies is stored in self.access_cookies.

        Uses log_msg as prefix to info level log message of accetance or
        rejection.
        """
        if (cookie in self.access_cookies):
            age = int(time.time()) - self.access_cookies[cookie]
            if (age <= (self.access_cookie_lifetime + 1)):
                self.logger.info(log_msg + " " + cookie +
                                 " ACCEPTED COOKIE (%ds old)" % age)
                return True
            # Expired...
            self.logger.info(log_msg + " " + cookie +
                             " EXPIRED COOKIE (%ds old > %ds)" %
                             (age, self.access_cookie_lifetime))
            # Keep cookie for 2x lifetim in order to generate
            # helpful expired message
            if (age > (self.access_cookie_lifetime * 2)):
                del self.access_cookies[cookie]
            return False
        else:
            self.logger.info(log_msg + " " + cookie + " REJECTED COOKIE")
            return False

    def access_token(self, cookie):
        """Make and store access token as proxy for the access cookie.

        Create an access token to act as a proxy for access cookie, add it to
        the dict of accepted access tokens with (cookie, current timestamp)
        as the value. Return the access token. Return None if cookie is not set.
        """
        if (cookie):
            token = self._generate_random_string(self.access_tokens)
            self.access_tokens[token] = (cookie, int(time.time()))
            return token
        else:
            return None

    def access_token_valid(self, token, log_msg):
        """Check token validity.

        Returns true if the token is valid. The set of allowed access tokens
        is stored in self.access_tokens.

        Uses log_msg as prefix to info level log message of acceptance or
        rejection.
        """
        if (token in self.access_tokens):
            (cookie, issue_time) = self.access_tokens[token]
            age = int(time.time()) - issue_time
            if (age <= (self.access_token_lifetime + 1)):
                self.logger.info(log_msg + " " + token +
                                 " ACCEPTED TOKEN (%ds old)" % age)
                return True
            # Expired...
            self.logger.info(log_msg + " " + token +
                             " EXPIRED TOKEN (%ds old > %ds)" %
                             (age, self.access_token_lifetime))
            # Keep token for 2x lifetim in order to generate
            # helpful expired message
            if (age > (self.access_token_lifetime * 2)):
                del self.access_tokens[token]
            return False
        else:
            self.logger.info(log_msg + " " + token + " REJECTED TOKEN")
            return False
