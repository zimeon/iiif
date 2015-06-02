"""IIIF Image Information Response

Model for IIIF Image API 'Image Information Response'.
Default version is 2.0 but also supports 2.1, 1.1 and 1.0
"""

import sys
import json
import re
import StringIO

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

    def add_services(self, info):
        """Add auth service descriptions to an IIIFInfo object
        """
        if (self.login_uri):
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



