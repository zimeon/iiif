"""IIIF error class

<?xml version="1.0" encoding="UTF8"?>
<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">
  <parameter>size</parameter>
  <text>Invalid size specified</text>
</error>
"""

import sys
import StringIO
from xml.etree.ElementTree import ElementTree, Element

# Namespace used in XML error response
I3F_NS = "http://library.stanford.edu/iiif/image-api/ns/"

class IIIFError:

    def __init__(self,code=500,parameter='unknown',text='',headers=None):
        self.code=code
        self.parameter=parameter
        self.text=text
        self.headers=headers if (headers is not None) else []
        self.content_type='text/xml'
        self.pretty_xml=True

    def __repr__(self):
        """XML representation of the error to be used in HTTP response
        """
        # Build tree
        spacing = ( "\n" if (self.pretty_xml) else "" )
        root = Element('error', { 'xmlns': I3F_NS } )
        root.text=spacing
        e_parameter = Element( 'parameter', {} )
        e_parameter.text = self.parameter
        e_parameter.tail = spacing
        root.append(e_parameter)
        if (self.text):
            e_text = Element( 'text', {} )
            e_text.text = self.text
            e_text.tail = spacing
            root.append(e_text)
        
        # Write out as XML document to return
        tree = ElementTree(root);
        xml_buf=StringIO.StringIO()
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        return(xml_buf.getvalue())
