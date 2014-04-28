"""IIIF Image Information Response

Model for info.json. The Image Information Response has been
in just the JSON format, with JSOD-LD extensions, since v1.1
of the Image API.
"""

import sys
import json
import re
import StringIO

# JSON-LD context
# 1.1
PARAMS = ['identifier','protocol','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile']
EVAL_PARAMS = set(['scale_factors','formats','qualities'])

class IIIFInfo(object):

    def __init__(self,level=1, identifier=None,width=None,height=None,
                 scale_factors=None,tile_width=None,tile_height=None,
                 formats=None,qualities=None,api_version='2.0',
                 conf=None,):
        # API version (used in level settings)
        self.api_version = api_version
        self.set_version_info()
        # explicit settings
        self.identifier = identifier
        self.width = width
        self.height = height
        self.scale_factors = scale_factors
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.formats = formats
        self.qualities = qualities
        self.level = level
        # defaults from conf dict if provided
        if (conf):
            for option in conf:
                if (option in EVAL_PARAMS):
                    self.__dict__[option]=eval(conf[option]) #FIXME - avoid eval
                else:
                    self.__dict__[option]=conf[option]

    def set_version_info(self):
        if (self.api_version=='1.1'):
            self.context = "http://library.stanford.edu/iiif/image-api/1.1/context.json"
            self.profile_prefix = "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level"
            self.profile_suffix = ""
            self.protocol = None
            self.required_params = ['identifier','width','height','profile']
        elif (self.api_version=='2.0'):
            self.context = "http://iiif.io/api/image/2.0/context.json"
            self.profile_prefix = "http://iiif.io/api/image/2/level"
            self.profile_suffix = ".json"
            self.protocol = "http://iiif.io/api/image"
            self.required_params = ['identifier','width','height','protocol','profile']

    @property
    def level(self):
        """Extract level number from profile URI

        Returns integer level number or raises excpetion
        """
        m = re.match(self.profile_prefix+r'(\d)'+self.profile_suffix+"$",self.profile)
        if (m):
            return int(m.group(1))
        raise Exception("Bad compliance profile URI, failed to extract level number")

    @level.setter
    def level(self, value):
        """Build profile URI from level
        
        Level should be an integer 0,1,2
        """
        self.profile = self.profile_prefix + ("%d" % value) + self.profile_suffix

    def set(self,param,value):
        if (param in EVAL_PARAMS):
            self.__dict__[param]=eval(value) #FIXME - avoid eval
        else:
            self.__dict__[param]=value

    def validate(self):
        """Validate this object as Image API data

        Raise Exception with helpful message if not valid.
        """
        errors = []
        for param in self.required_params:
            if (param not in self.__dict__ or
                self.__dict__[param] is None):
                errors.append("missing %s parameter" % (param))
        if (len(errors)>0):
            raise Exception("Bad data for inso.json: "+", ".join(errors))
        return True

    def as_json(self, validate=True):
        """Return JSON serialization
        
        Will raise exception if insufficient parameters are present to
        have a valid info.json response (unless validate is False).
        """
        if (validate):
            self.validate()
        json_dict = {}
        json_dict['@context']=self.context
        if (self.identifier):
            json_dict['@id']=self.identifier
        for param in PARAMS:
            if (param in self.__dict__ and 
                self.__dict__[param] is not None and
                param!='identifier'):
                json_dict[param] = self.__dict__[param]
        return( json.dumps(json_dict, sort_keys=True, indent=2 ) )
