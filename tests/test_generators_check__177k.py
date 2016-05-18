"""Test code for iiif.generators.check__177k."""
import unittest

from iiif.generators.check__177k import PixelGen


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_size(self):
        """Test size."""
        gen = PixelGen()
        self.assertEqual(len(gen.size), 2)
        self.assertTrue(int(gen.size[0]) > 170000)
        self.assertTrue(int(gen.size[0]) < 180000)
