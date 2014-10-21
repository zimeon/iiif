"""Test code for iiif_error.py"""
import unittest

from iiif.manipulator import IIIFManipulator
from iiif.request import IIIFRequest

class TestAll(unittest.TestCase):

    def test001(self):
        m = IIIFManipulator()
        m.request = IIIFRequest()
        self.assertEqual( m.quality_to_apply(), 'default' )

    def test100(self):
        # v1.0 tests
        m = IIIFManipulator(api_version='1.0')
        m.request = IIIFRequest()
        self.assertEqual( m.quality_to_apply(), 'native' )

    def test110(self):
        # v1.1 tests
        m = IIIFManipulator(api_version='1.1')
        m.request = IIIFRequest()
        self.assertEqual( m.quality_to_apply(), 'native' )


# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
