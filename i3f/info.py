"""IIIF information response class

Supports both JSON and XML responses:


"""

import sys
import json
import StringIO
from xml.etree.ElementTree import ElementTree, Element

# Namespace used in XML error response
I3F_NS = "http://library.stanford.edu/iiif/image-api/ns/"
PARAMS = ['identifier','width','height','scale_factors','tile_width','tile_height','formats','qualities','profile']
# A lookup for which values take a list, and also a traslation table for
# the XML element names for list elements
LIST_PARAMS = {'scale_factors':'scale_factor','formats':'format','qualities':'quality'}

class I3fInfo:

    def __init__(self,identifier=None,width=None,height=None,
                 scale_factors=None,tile_width=None,tile_height=None,
                 formats=None,qualities=None):
        self.identifier = identifier
        self.width = width
        self.height = height
        self.scale_factors = scale_factors
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.formats = formats
        self.qualities = qualities
        self.profile = 'http://library.stanford.edu/iiif/image-api/compliance.html#level1'
        #
        self.pretty_xml=True

    def as_json(self):
        json_dict = {}
        for param in PARAMS:
            if (param in self.__dict__ and self.__dict__[param] is not None):
                json_dict[param] = self.__dict__[param]
        return( json.dumps(json_dict, sort_keys=True, indent=2 ) )

    def as_xml(self):
        """Return XML string for IIIF info request 

        <?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://library.stanford.edu/iiif/image-api/ns/">
  <identifier>1E34750D-38DB-4825-A38A-B60A345E591C</identifier>
  <width>6000</width>
  <height>4000</height>
  <scale_factors>
    <scale_factor>1</scale_factor>
    <scale_factor>2</scale_factor>
    <scale_factor>4</scale_factor>
  </scale_factors>
  <tile_width>1024</tile_width>
  <tile_height>1024</tile_height>
  <formats>
    <format>jpg</format>
    <format>png</format>
  </formats>
  <qualities>
    <quality>native</quality>
    <quality>grey</quality>
  </qualities>
</info>
"""
        # Build tree
        spacing = ( "\n" if (self.pretty_xml) else "" )
        root = Element('info', { 'xmlns': I3F_NS } )
        root.text=spacing
        for param in PARAMS:
            if (param in self.__dict__ and self.__dict__[param] is not None):
                value = self.__dict__[param]
                if (value is not None):
                    element = Element( param, {} )
                    element.tail = spacing
                    if (param in LIST_PARAMS):
                        element.text = spacing
                        for v in value:
                            sub = Element( LIST_PARAMS[param], {} )
                            sub.text = str(v)
                            sub.tail = spacing
                            element.append(sub)
                    else:
                        element.text = str(value)
                    root.append(element)

        # Write out as XML document to return
        tree = ElementTree(root);
        xml_buf=StringIO.StringIO()
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        return(xml_buf.getvalue())

    def __repr__(self):
        """Default is JSON per as_json()"""
        return(self.as_json())
