"""Test code for null iiif.manipulator"""
import unittest

from iiif.manipulator_pil import IIIFManipulatorPIL

class TestAll(unittest.TestCase):

    def test01_init(self):
        m = IIIFManipulatorPIL()
        self.assertEqual( m.api_version, '2.0' )
