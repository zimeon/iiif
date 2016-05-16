"""Test code for netpbm based IIIF Image manipulator."""
import unittest

from iiif.manipulator_netpbm import IIIFManipulatorNetpbm


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_init(self):
        """Initialize."""
        m = IIIFManipulatorNetpbm()
        self.assertTrue(m.api_version)
