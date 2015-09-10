"""IIIF error class.

In IIIF Image API version 1.0 the specification mandates an XML response
following the format:

  <?xml version="1.0" encoding="UTF-8"?>
  <error xmlns="http://library.stanford.edu/iiif/image-api/ns/">
    <parameter>size</parameter>
    <text>Invalid size specified</text>
  </error>

Later versions of the specification do not specify the response format but
suggest a human readable message. For now we use the 1.0 format for all
API versions.

FIXME - improve messages for api_version>1.0. Do not include old namespace.
"""

import sys
from xml.etree.ElementTree import ElementTree, Element
try: #python2
    import BytesIO as io
    # Must check for python2 first as io exists but is wrong one
except ImportError: #python3
    import io

# Namespace used in XML error response
I3F_NS = "http://library.stanford.edu/iiif/image-api/ns/"

class IIIFError(Exception):

    """Class to represent IIIF error conditions."""

    def __init__(self,code=500,parameter='unknown',text='',headers=None):
        """Initialize IIIFError object.

        Keyword arguments:
        code -- HTTP error/status code, should always specify
        parameter -- parameter causing error to help with debugging
        test -- human explanation to help with debugging
        headers -- additional HTTP headers
        """
        self.code=code
        self.parameter=parameter
        self.text=text
        self.headers=headers if (headers is not None) else []
        self.content_type='text/xml'
        self.pretty_xml=True

    def __str__(self):
        """XML representation of the error to be used in HTTP response."""
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
        xml_buf=io.BytesIO()
        if (sys.version_info < (2,7)):
            tree.write(xml_buf,encoding='UTF-8')
        else:
            tree.write(xml_buf,encoding='UTF-8',xml_declaration=True,method='xml')
        return(xml_buf.getvalue().decode('utf-8'))


class IIIFZeroSizeError(IIIFError):

    """Sub-class of IIIFError to indicate request for a zero-size image."""

    pass
