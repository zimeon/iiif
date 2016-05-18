"""Image generator for 3x3 check pattern with self-similar repeat.

See <check.py> for details. This version overrides size
"""

from .check import PixelGen as PixelGenBase


class PixelGen(PixelGenBase):
    """Pixel generation class for 3**11 check pattern."""

    def __init__(self):
        """Set size."""
        self.sz = 3**11  # 177k
