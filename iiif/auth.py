"""IIIF Authentication

Base authentication object which does not actually implement and
authentication scheme but is the foundation for specific sub-classes
for different schemes.
"""

import json
import re

class IIIFAuth(object):

    def __init__(self):
        """Create IIIFAuth object
          
        """
        self.profile_base = 'http://iiif.io/api/image/2/auth/'
        self.name = "image server"
        self.login_uri = None
        self.logout_uri = None
        self.client_id_uri = None
        self.access_token_uri = None

    def add_services(self, info, logged_in=False):
        """Add auth service descriptions to an IIIFInfo object
        """
        if (self.login_uri and not logged_in):
            info.add_service( self.login_service_description() )
        if (self.logout_uri):
            info.add_service( self.logout_service_description() )
        if (self.client_id_uri):
            info.add_service( self.client_id_service_description() )
        if (self.access_token_uri):
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
            response.set_cookie('loggedin', account, secret="SECRET_HERE")
        data_str = json.dumps(data)

        if callback:
            return self.send("%s(%s);" % (callback, data_str), ct="application/javascript")
        else:
            return self.send(data_str, ct="application/json")

    def host_port_prefix(self,host,port,prefix):
        """Return URI composed of scheme, server, port, and prefix"""
        uri = "http://"+host
        if (host!=80):
            uri += ':'+str(port)
        if (prefix):
            uri += '/'+prefix
        return uri

    # Override with method to implement
    client_id_handler=None

    # Override with method to implement
    home_handler=None

    def is_authn(self): 
        """Check to see if user if authenticated

        Null implementation that always returns False, must override
        to implement authorization.
        """
        return False

    def is_authz(self): 
        """Check to see if user if authenticated and authorized

        Null implementation that says that any authenticated user is
        authorized.
        """
        return self.is_authn()





