"""IIIF information response class

Model for info.json. Just JSON format since API v1.1.
"""

import sys
import json
import StringIO

# JSON-LD context
CONTEXT = "http://library.stanford.edu/iiif/image-api/1.1/context.json"
PARAMS = ['identifier','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile']
EVAL_PARAMS = set(['scale_factors','formats','qualities'])

class IIIFInfo:

    def __init__(self,identifier=None,width=None,height=None,
                 scale_factors=None,tile_width=None,tile_height=None,
                 formats=None,qualities=None,conf=None):
        # explicit settings
        self.identifier = identifier
        self.width = width
        self.height = height
        self.scale_factors = scale_factors
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.formats = formats
        self.qualities = qualities
        self.profile = 'http://library.stanford.edu/iiif/image-api/compliance.html#level1'
        self.pretty_xml=True
        # defaults from conf dict if provided
        if (conf):
            for option in conf:
                if (option in EVAL_PARAMS):
                    self.__dict__[option]=eval(conf[option]) #FIXME - avoid eval
                else:
                    self.__dict__[option]=conf[option]

    def set(self,param,value):
        if (param in EVAL_PARAMS):
            self.__dict__[param]=eval(value) #FIXME - avoid eval
        else:
            self.__dict__[param]=value

    def as_json(self):
        """return JSON serialization"""
        json_dict = {}
        json_dict['@context']=CONTEXT
        for param in PARAMS:
            if (param in self.__dict__ and self.__dict__[param] is not None):
                json_dict[param] = self.__dict__[param]
        return( json.dumps(json_dict, sort_keys=True, indent=2 ) )
