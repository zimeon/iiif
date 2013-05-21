"""Test code for i3f_error.py"""
import unittest

from i3f.error import I3fError

class TestAll(unittest.TestCase):

    def test1(self):
        # Just do the trivial XML test
        ie = I3fError()
        self.assertEqual( str(ie), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n<parameter>unknown</parameter>\n</error>')
        ie.code='501'
        ie.parameter='size'
        ie.text='Negative size not implemented'
        self.assertEqual( str(ie), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<error xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n<parameter>size</parameter>\n<text>Negative size not implemented</text>\n</error>')

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
