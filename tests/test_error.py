"""Test code for iiif.error."""
import unittest
import re

from iiif.error import IIIFError

class TestAll(unittest.TestCase):

    def test1(self):
        # Just do the trivial XML test
        ie = IIIFError()
        # Encoding value should be capital UTF-8 per
        # http://www.w3.org/TR/2006/REC-xml11-20060816/#NT-EncName
        # but in python3 it comes out at utf-8
        xml = re.sub(r'utf-8','UTF-8',str(ie))
        self.assertEqual( xml, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n<parameter>unknown</parameter>\n</error>')
        ie.code='501'
        ie.parameter='size'
        ie.text='Negative size not implemented'
        xml = re.sub(r'utf-8','UTF-8',str(ie))
        self.assertEqual( xml, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n<parameter>size</parameter>\n<text>Negative size not implemented</text>\n</error>')

