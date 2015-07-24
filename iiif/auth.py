"""IIIF Authentication

Base authentication object which does not actually implement and
authentication scheme but is a foundation for specific sub-classes
for different schemes.
"""

import json
import logging
import random
import re

class IIIFAuth(object):

    def __init__(self, cookie_prefix=None):
        """Create IIIFAuth object
          
        """
        self.profile_base = 'http://iiif.io/api/image/2/auth/'
        self.name = "image server"
        self.login_uri = None
        self.logout_uri = None
        self.client_id_uri = None
        self.access_token_uri = None
        self.logger = logging.getLogger(__name__)
        # Need to have different cookie names for each auth domain
        # running on the same server
        self.set_cookie_prefix(cookie_prefix)
        self.auth_cookie_name = self.cookie_prefix+'loggedin'
        self.token_cookie_name = self.cookie_prefix+'token'

    def set_cookie_prefix(self,cookie_prefix=None):
        """Set a random cookie prefix unless one is specified

        In order to run multiple demonstration auth services on the
        same server we need to have different cookie names for each
        auth domain. Unless cookie_prefix is set, generate a random
        one.
        """
        if (cookie_prefix is None):
            self.cookie_prefix = "%06d_" % int(random.random()*1000000)
        else:
            self.cookie_prefix = cookie_prefix

    def add_services(self, info):
        """Add auth service descriptions to an IIIFInfo object

        FIXME - Should login, token and logout all always be present
        or should that depend on that login status? For now keep them
        all always present.
        """
        #authn = self.info_authn()
        if (self.login_uri): # and not authn):
            info.add_service( self.login_service_description() )
        if (self.logout_uri): # and authn):
            info.add_service( self.logout_service_description() )
        if (self.client_id_uri):
            info.add_service( self.client_id_service_description() )
        if (self.access_token_uri): # and not authn):
            info.add_service( self.access_token_service_description() )

    def login_service_description(self):
        return( { "@id": self.login_uri,
                  "profile": self.profile_base+'login',
                  "label": 'Login to '+self.name
                } )

    def logout_service_description(self):
        return( { "@id": self.logout_uri,
                  "profile": self.profile_base+'logout',
                  "label": 'Logout from '+self.name
                } )

    def client_id_service_description(self):
        return( { "@id": self.client_id_uri,
                  "profile": self.profile_base+'clientId'
                } )

    def access_token_service_description(self):
        return( { "@id": self.access_token_uri,
                  "profile": self.profile_base+'token'
                } )

    def access_token_response(self, query, cookies):
        """ Client requests a token to send with info.json request

        If we have one then we copy it from this request. If a callback
        is specified then we wrap as JSONP.
        """
        callback = query.get('callback', '')
        authcode = query.get('code', '')
        account = ''
        try:
            account = request.get_cookie('account', secret="SECRET_HERE")
            response.delete_cookie('account', secret="SECRET_HERE")
        except:
            pass
        if not account:
            data = {"error":"client_unauthorized","error_description": "No login details received"}
        else:
            data = {"access_token":account, "token_type": "Bearer", "expires_in": 3600}
            # Set the cookie for the image content
            response.set_cookie(self.auth_cookie_name, account, secret="SECRET_HERE")
        data_str = json.dumps(data)

        if callback:
            return self.send("%s(%s);" % (callback, data_str), ct="application/javascript")
        else:
            return self.send(data_str, ct="application/json")

    def scheme_host_port_prefix(self, scheme='http', host='host', port=None, prefix=None):
        """Return URI composed of scheme, server, port, and prefix"""
        uri = scheme+'://'+host
        if (port and not ((scheme=='http' and port==80) or
                          (scheme=='https' and port==443))):
            uri += ':'+str(port)
        if (prefix):
            uri += '/'+prefix
        return uri

    # Override with method to implement
    client_id_handler=None

    # Override with method to implement
    home_handler=None

    def info_authn(self): 
        """Check to see if user is authenticated for info.json

        Null implementation that always returns False, must override
        to implement authorization.
        """
        return False

    def info_authz(self): 
        """Check to see if user is authenticated and authorized for info.json

        Null implementation that says that any authenticated user is
        authorized.
        """
        return self.info_authn()

    def image_authn(self): 
        """Check to see if user is authenticated for image requests

        Null implementation that always returns False, must override
        to implement authorization.
        """
        return False

    def image_authz(self): 
        """Check to see if user is authenticated and authorized for image requests

        Null implementation that says that any authenticated user is
        authorized.
        """
        return self.image_authn()





