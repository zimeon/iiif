"""Test code for null iiif.manipulator_netpbm"""
import unittest

from iiif.manipulator_netpbm import IIIFManipulatorNetpbm

class TestAll(unittest.TestCase):

    def test01_init(self):
        m = IIIFManipulatorNetpbm()
        self.assertEqual( m.api_version, '2.0' )
