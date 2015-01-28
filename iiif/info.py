"""IIIF Image Information Response

Model for IIIF Image API 'Image Information Response'.
Default version is 2.0 but also supports 1.1 and 1.0
"""

import sys
import json
import re
import StringIO


def _parse_int_array(info,json_data):
    return [int(x) for x in json_data] #force simple array

def _parse_noop(info,json_data):
    #format is already what we want
    return json_data

def _parse_tiles(info,json_data):
    # Expect common case in 2.0 to map to 1.1 idea of tile_width,
    # tile_height and scale_factors. This is the case when len()==1
    if (len(json_data)==1):
        # set items as side-effect
        info.tile_width = json_data[0]['width']
        info.tile_height = json_data[0]['width']
        info.scale_factors = json_data[0]['scaleFactors']
    else:
        raise Exception("FIXME - support for multiple tile sizes not imeplemented")
    return json_data

def _parse_service(info,json_data):
    return json_data

def _parse_profile(info,json_data):
    # FIXME - for now simply extract first element and the profile,
    # ignore extra info in 2.0
    return str(json_data[0])

# Configuration information for API versions
CONF = {
    '1.0': {
        'params': ['identifier','protocol','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile'],
        'array_params': set(['scale_factors','formats','qualities']),
        'complex_params': {
            'scale_factors': _parse_int_array,
            'formats': _parse_noop, #array of str
            'qualities': _parse_noop, #array of str
            },
        'profile_prefix': "http://library.stanford.edu/iiif/image-api/compliance.html#level",
        'profile_suffix': "",
        'protocol': None,
        'required_params': ['identifier','width','height','profile'],
        },
    '1.1': {
        'params': ['identifier','protocol','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile'],
        'array_params': set(['scale_factors','formats','qualities']),
        'complex_params': {
            'scale_factors': _parse_int_array,
            'formats': _parse_noop, #array of str
            'qualities': _parse_noop, #array of str
            },
        'context': "http://library.stanford.edu/iiif/image-api/1.1/context.json",
        'profile_prefix': "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level",
        'profile_suffix': "",
        'protocol': None,
        'required_params': ['identifier','width','height','profile'],
        },
    '2.0': {
        'params': ['identifier','protocol','width','height','profile','sizes','tiles','service'],
        'array_params': set(['sizes','tiles','service','scale_factors','formats','qualities','supports']), #scale_factors isn't in API but used internally
        'complex_params': {
            'sizes': _parse_noop,
            'tiles': _parse_tiles,
            'profile': _parse_profile,
            'service': _parse_service,
            },
        'context': "http://iiif.io/api/image/2/context.json",
        'profile_prefix': "http://iiif.io/api/image/2/level",
        'profile_suffix': ".json",
        'protocol': "http://iiif.io/api/image",
        'required_params': ['identifier','protocol','width','height','profile'],
        }
}
    
class IIIFInfo(object):

    def __init__(self,api_version='2.0',profile=None,level=1,conf=None,
                 server_and_prefix='',
                 identifier=None,width=None,height=None,tiles=None,
                 sizes=None,service=None,id=None,
                 # legacy params from 1.1
                 scale_factors=None,tile_width=None,tile_height=None,
                 # 1.1 and 2.0
                 formats=None,qualities=None,
                 # 2.0 only
                 supports=None
                 ):
        """Create IIIFInfo object

          api_version - defaults to 2.0 but may be set to 1.1
          profile - usually not set but overrides handling via level
            (2.0 complex profile not supported except by explicitly
            passing in an array that matches JSON required)
          level - default 1, generates compliance level for simple profile
          
        """
        # API version (used in level settings)
        if (api_version not in CONF):
            raise Exception("Unknown IIIF Image API version '%s', versions supported are ('%s')" % (api_version,sorted(CONF.keys())))
        self.api_version = api_version
        self.set_version_info()
        if (profile is not None):
            # Explicit profile setting overrides any level set
            # or default level
            self.profile = profile
        else:
            self.level = level
        # explicit settings
        self.server_and_prefix = server_and_prefix
        self.identifier = identifier
        self.width = width
        self.height = height
        self.tiles = tiles
        self.sizes = sizes
        self.service = service
        # legacy params for 1.1
        self.scale_factors = scale_factors
        self.tile_width = tile_width
        self.tile_height = tile_height
        # 1.1 and 2.0
        self.formats = formats
        self.qualities = qualities
        # 2.0 only
        self.supports = supports
        # defaults from conf dict if provided
        if (conf):
            for option in conf:
                self.__dict__[option]=conf[option]
        if (id is not None):
            self.id = id

    @property
    def id(self):
        id = ''
        if (self.server_and_prefix is not None and
            self.server_and_prefix!=''):
            id += self.server_and_prefix + '/'
        if (self.identifier is not None):    
            id += self.identifier
        return id

    @id.setter
    def id(self,value):
        """Split into server_and_prefix and identifier"""
        i = value.rfind('/')
        if (i>0):
            self.server_and_prefix=value[:i]
            self.identifier=value[(i+1):]
        elif (i==0):
            self.server_and_prefix=''
            self.identifier=value[(i+1):]
        else:
            self.server_and_prefix=''
            self.identifier=value

    def set_version_info(self, api_version=None):
        """Set up normal values for given api_version

        Will use current value of self.api_version if a version number
        is not specified in the call.
        """
        if (api_version is None):
            api_version = self.api_version
        self.params = CONF[api_version]['params']
        self.array_params = CONF[api_version]['array_params']
        self.complex_params = CONF[api_version]['complex_params']
        for a in ('context','profile_prefix','profile_suffix',
                  'protocol','required_params'):
            if (a in CONF[api_version]):
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
        if (param in self.array_params):
            # If we have an array then set directly, else eval. Perhaps not
            # pythonic to do a type check for array here but want to avoid
            # accidentally iterating on chars in string etc..
            if (type(value) == str):
                self.__dict__[param]=eval(value) #FIXME - avoid eval
            else:
                self.__dict__[param]=value
        else:
            self.__dict__[param]=value

    def validate(self):
        """Validate this object as Image API data

        Raise Exception with helpful message if not valid.
        """
        errors = []
        for param in self.required_params:
            if (not hasattr(self,param) or getattr(self,param) is None):
                errors.append("missing %s parameter" % (param))
        if (len(errors)>0):
            raise Exception("Bad data for info.json: "+", ".join(errors))
        return True

    def as_json(self, validate=True):
        """Return JSON serialization
        
        Will raise exception if insufficient parameters are present to
        have a valid info.json response (unless validate is False).
        """
        if (self.api_version=='2.0' and not self.tiles and
            self.tile_width and self.scale_factors):
            # make 2.0 tiles data from 1.1 like data
            self.tiles = [ { 'width': int(self.tile_width), #FIXME - int() is fudge, data should be int
                             'scaleFactors': self.scale_factors } ]
        if (validate):
            self.validate()
        json_dict = {}
        if (self.api_version>'1.0'):
            json_dict['@context']=self.context
        params_to_write = set(self.params)
        params_to_write.discard('identifier')
        if (self.identifier):
            if (self.api_version=='1.0'):
                json_dict['identifier']=self.identifier # local id
            else:
                json_dict['@id']=self.id # URI
        params_to_write.discard('profile')
        if (self.profile):
            if (self.api_version<'2.0'):
                json_dict['profile']=self.profile
            else:
                json_dict['profile']=[self.profile] #FIXME - need to support extra profile features
                d = {}
                if (self.formats is not None):
                    d['formats']=self.formats
                if (self.qualities is not None):
                    d['qualities']=self.qualities
                if (self.supports is not None):
                    d['supports']=self.supports
                if (len(d)>0):
                    json_dict['profile'].append(d)
                params_to_write.discard('formats')
                params_to_write.discard('qualities')
                params_to_write.discard('supports')
        for param in params_to_write:
            if (hasattr(self,param) and 
                self.__dict__[param] is not None):
                json_dict[param] = self.__dict__[param]
        return( json.dumps(json_dict, sort_keys=True, indent=2 ) )

    def read(self, fh, api_version=None):
        """Read info.json from file like object supporting fh.read()

        If version is set then the parsing will assume this API version. If
        there is a @context specified then an exception will be raised unless
        it matches. If no known @context is present and no api_version set 
        then an exception will be raised.
        """
        j = json.load(fh)
        self.context=None
        if (self.api_version!='1.0'):
            self.context = j['@context']
            # Determine API version from context
            api_version_read = None
            for v in CONF:
                if (v>'1.0' and self.context==CONF[v]['context']):
                    api_version_read = v
            if (api_version_read is None):
                if (api_version is not None):
                    self.api_version = api_version
                else:
                    raise Exception("Unknown @context, cannot determine API version (%s)"%(self.context))
            else:
                if (api_version is not None and
                    api_version != api_version_read):
                    raise Exception("Expected API version '%s' but got context for API version '%s'" % (api_version,api_version_read))
                else:
                    self.api_version = api_version_read
        self.set_version_info()
        #
        if (self.api_version=='1.0'):
            self.id = j['identifier']
        else:
            self.id = j['@id']
        for param in self.params:
            if (param == 'indentifier' or
                param == '@id'):
                continue #dealt with above
            if (param in j):
                if (param in self.complex_params):
                    # use function ref in complex_params to parse
                    self.set(param, self.complex_params[param](self,j[param]))
                else:
                    self.set(param,j[param])
        return True

        
