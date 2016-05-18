"""Test code for iiif.error."""
import unittest
import re

from iiif.error import IIIFError


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_str(self):
        """Test str method."""
        e = IIIFError()
        self.assertEqual(str(e), 'UNKNOWN_ERROR, parameter=unknown, code=500')
        e = IIIFError(text='aa', parameter='bb', code=404)
        self.assertEqual(str(e), 'aa, parameter=bb, code=404')

    def test02_xml(self):
        """Test xml output used in Image API 1.0."""
        # Just do the trivial XML test
        e = IIIFError()
        # Encoding value should be capital UTF-8 per
        # http://www.w3.org/TR/2006/REC-xml11-20060816/#NT-EncName
        # but in python3 it comes out at utf-8
        xml = re.sub(r'utf-8', 'UTF-8', e.as_xml())
        self.assertEqual(xml,
                         '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n'
                         '<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n'
                         '<parameter>unknown</parameter>\n</error>')
        e.code = '501'
        e.parameter = 'size'
        e.text = 'Negative size not implemented'
        xml = re.sub(r'utf-8', 'UTF-8', e.as_xml())
        self.assertEqual(xml,
                         '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n'
                         '<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n'
                         '<parameter>size</parameter>\n'
                         '<text>Negative size not implemented</text>\n</error>')

    def test03_txt(self):
        """Test txt output."""
        e = IIIFError()
        msg = 'IIIF Image Server Error\n\nUNKNOWN_ERROR\n\nparameter=unknown\ncode=500\n\n'
        self.assertEqual(e.as_txt(), msg)
        e = IIIFError(headers={'cc': 'dd', 'a': 'b'})
        self.assertEqual(e.as_txt(), msg + 'header a=b\nheader cc=dd\n')

    def test04_image_server_response(self):
        """Test image_server_response."""
        e = IIIFError(headers={'x': 'y'})
        (response, status, headers) = e.image_server_response(
            api_version='1.0')
        self.assertTrue(re.match(r'''<\?xml version''', response))
        self.assertEqual(status, 500)
        self.assertEqual(headers, {'x': 'y', 'Content-Type': 'text/xml'})
        (response, status, headers) = e.image_server_response(
            api_version='2.0')
        self.assertTrue(re.match(r'''IIIF Image Server Error\n''', response))
        self.assertEqual(status, 500)
        self.assertEqual(headers, {'x': 'y', 'Content-Type': 'text/plain'})
