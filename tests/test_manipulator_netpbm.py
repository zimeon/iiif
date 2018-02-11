"""Test code for netpbm based IIIF Image manipulator."""
import unittest

from iiif.error import IIIFError
from iiif.manipulator_netpbm import IIIFManipulatorNetpbm


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_init(self):
        """Initialize."""
        m = IIIFManipulatorNetpbm()
        self.assertTrue(m.api_version)

    def test_do_first_empty(self):
        """First step with no image."""
        m = IIIFManipulatorNetpbm()
        # no image
        self.assertRaises(IIIFError, m.do_first)

        # Don't actually do a test as we won't assume netpbm installed
        #
        # add image, get size
        # m.srcfile = 'testimages/test1.png'
        # self.assertEqual(m.do_first(), None)
        # self.assertEqual(m.width, 175)
        # self.assertEqual(m.height, 131)
