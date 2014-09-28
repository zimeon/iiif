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
CONF = {
    '1.1': {
        'params': ['identifier','protocol','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile'],
        'eval_params': set(['sizes','scale_factors','formats','qualities']),
        'context': "http://library.stanford.edu/iiif/image-api/1.1/context.json",
        'profile_prefix': "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level",
        'profile_suffix': "",
        'protocol': None,
        'required_params': ['identifier','width','height','profile'],
        },
    '2.0': {
        'params': ['identifier','protocol','width','height','sizes','scale_factors','tile_width','tile_height','formats','qualities','profile'],
        'eval_params': set(['sizes','scale_factors','formats','qualities']),
        'context': "http://iiif.io/api/image/2.0/context.json",
        'profile_prefix': "http://iiif.io/api/image/2/level",
        'profile_suffix': ".json",
        'protocol': "http://iiif.io/api/image",
        'required_params': ['identifier','width','height','protocol','profile'],
        }
}
    
class IIIFInfo(object):

    def __init__(self,level=1, identifier=None,width=None,height=None,
                 scale_factors=None,tile_width=None,tile_height=None,
                 formats=None,qualities=None,api_version='2.0',
                 conf=None,):
        # API version (used in level settings)
        if (api_version not in CONF):
            raise Exception("Unknown IIIF Image API version '%s', versions supported are ('%s')" % (api_version,sorted(CONF.keys())))
        self.api_version = api_version
        self.params = CONF[api_version]['params']
        self.eval_params = CONF[api_version]['eval_params']
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
                if (option in self.eval_params):
                    self.__dict__[option]=eval(conf[option]) #FIXME - avoid eval
                else:
                    self.__dict__[option]=conf[option]

    def set_version_info(self, api_version=None):
        """Set up normal values for given api_version

        Will use current value of self.api_version if a version number
        is not specified in the call.
        """
        if (api_version is None):
            api_version = self.api_version
        for a in ('context','profile_prefix','profile_suffix',
                  'protocol','required_params'):
            self.set(a,CONF[api_version][a])

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
        if (param in self.eval_params):
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
        for param in self.params:
            if (param in self.__dict__ and 
                self.__dict__[param] is not None and
                param!='identifier'):
                json_dict[param] = self.__dict__[param]
        return( json.dumps(json_dict, sort_keys=True, indent=2 ) )

    def read(self, fh):
        """Read info.json from file like object supporting fh.read()
        """
        j = json.load(fh)
        self.context = j['@context']
        # Determine API version from context
        self.id = j['@id']
        self.protocol = j['protocol']
        self.width = j['width']
        self.height = j['height']
        for hw in j['sizes']:
            pass
        return True

