"""Really dumb test code for iiif.generators.julia__m161_1p04.py."""
import unittest
import cmath

from iiif.generators.julia_m161_1p04 import PixelGen


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_set_c(self):
        """Test set_c."""
        gen = PixelGen()
        gen.set_c(complex(0, 1))
        self.assertAlmostEqual(gen.c.real, -0.161)
        self.assertAlmostEqual(gen.c.imag, 1.04)
