"""IIIF Image API error class.

In IIIF Image API version 1.1 and above the specification do not
mandate a particular format but suggest a human readable message.
Suitable output is provided in plain text by error.as_txt().

In IIIF Image API version 1.0 the specification mandates an XML
response following the format:

  <?xml version="1.0" encoding="UTF-8"?>
  <error xmlns="http://library.stanford.edu/iiif/image-api/ns/">
    <parameter>size</parameter>
    <text>Invalid size specified</text>
  </error>

This format is provided by error.as_xml().
"""

import sys
from xml.etree.ElementTree import ElementTree, Element
try:  # python2
    import BytesIO as io
    # Must check for python2 first as io exists but is wrong one
except ImportError:  # python3
    import io

# Namespace used in v1.0 XML error response
I3F_NS = "http://library.stanford.edu/iiif/image-api/ns/"


class IIIFError(Exception):
    """Class to represent IIIF error conditions."""

    def __init__(self, code=500, parameter='unknown', text='', headers=None):
        """Initialize IIIFError object.

        Keyword arguments:
        code -- HTTP error/status code, should always specify
        parameter -- parameter causing error to help with debugging
        test -- human explanation to help with debugging
        headers -- additional HTTP headers
        """
        self.code = code
        self.parameter = parameter
        self.text = text
        self.headers = headers if (headers is not None) else ()
        self.content_type = 'text/plain'
        self.pretty_xml = True

    def image_server_response(self, api_version=None):
        """Response, code and headers for image server error response.

        api_version selects the format (XML of 1.0). The return value is
        a tuple of
          response - body of HTTP response
          status - the HTTP status code
          headers - a dict of HTTP headers which will include the Content-Type

        As a side effect the routine sets self.content_type
        to the correct media type for the response.
        """
        headers = dict(self.headers)
        if (api_version < '1.1'):
            headers['Content-Type'] = 'text/xml'
            response = self.as_xml()
        else:
            headers['Content-Type'] = 'text/plain'
            response = self.as_txt()
        return(response, self.code, headers)

    def as_xml(self):
        """XML representation of the error to be used in HTTP response.

        This XML format follows the IIIF Image API v1.0 specification,
        see <http://iiif.io/api/image/1.0/#error>
        """
        # Build tree
        spacing = ("\n" if (self.pretty_xml) else "")
        root = Element('error', {'xmlns': I3F_NS})
        root.text = spacing
        e_parameter = Element('parameter', {})
        e_parameter.text = self.parameter
        e_parameter.tail = spacing
        root.append(e_parameter)
        if (self.text):
            e_text = Element('text', {})
            e_text.text = self.text
            e_text.tail = spacing
            root.append(e_text)
        # Write out as XML document to return
        tree = ElementTree(root)
        xml_buf = io.BytesIO()
        if (sys.version_info < (2, 7)):
            tree.write(xml_buf, encoding='UTF-8')
        else:
            tree.write(xml_buf, encoding='UTF-8',
                       xml_declaration=True, method='xml')
        return(xml_buf.getvalue().decode('utf-8'))

    def as_txt(self):
        """Text rendering of error response.

        Designed for use with Image API version 1.1 and above where the
        error response is suggested to be text or html but not otherwise
        specified. Intended to provide useful information for debugging.
        """
        s = "IIIF Image Server Error\n\n"
        s += self.text if (self.text) else 'UNKNOWN_ERROR'
        s += "\n\n"
        if (self.parameter):
            s += "parameter=%s\n" % self.parameter
        if (self.code):
            s += "code=%d\n\n" % self.code
        for header in sorted(self.headers):
            s += "header %s=%s\n" % (header, self.headers[header])
        return s

    def __str__(self):
        """Short human readable version of IIIF error.

        This rendering does not include the HTTP status code or header
        values in output. The intention is that image server implementations
        will use image_server_response(api_version) instead.
        """
        s = self.text if (self.text) else 'UNKNOWN_ERROR'
        if (self.parameter and self.parameter != 'unknown'):
            s += ", parameter=%s" % self.parameter
        return s


class IIIFZeroSizeError(IIIFError):
    """Sub-class of IIIFError to indicate request for a zero-size image."""

    pass
