#!/usr/bin/env python
"""Code to check algorithm for implementing maxArea, maxHeight, maxWidth.

See: http://iiif.io/api/image/3.0/#technical-properties
"""
import unittest


def aspect_ratio_preserving_resize(width, height, scale):
    """Acpect ratio preserving scaling of width,height."""
    if (width <= height):
        w = int(width * scale)
        h = int(height * float(w) / float(width) + 0.5)
    else:
        h = int(height * scale)
        w = int(width * float(h) / float(height) + 0.5)
    return(w, h)


def max(width, height, maxArea=None, maxHeight=None, maxWidth=None):
    """Return /max/ size as w,h given region width,height and constraints."""
    # default without constraints
    (w, h) = (width, height)
    # use size constraints if present, else full
    if maxArea and maxArea < (w * h):
        # approximate area limit, rounds down to avoid possibility of
        # slightly exceeding maxArea
        scale = (float(maxArea) / float(w * h)) ** 0.5
        w = int(w * scale)
        h = int(h * scale)
    if maxWidth:
        if not maxHeight:
            maxHeight = maxWidth
        if maxWidth < w:
            # calculate wrt original width, height rather than
            # w, h to avoid compounding rounding issues
            w = maxWidth
            h = int(float(height * maxWidth) / float(width) + 0.5)
        if maxHeight < h:
            h = maxHeight
            w = int(float(width * maxHeight) / float(height) + 0.5)
    # w, h is possibly constrained size
    return(w, h)


class TestStringMethods(unittest.TestCase):
    """Test it..."""

    def max(self, width, height, maxArea=None, maxHeight=None, maxWidth=None):
        """Wrapper around max that checks values returned against constraints."""
        (w, h) = max(width, height, maxArea, maxHeight, maxWidth)
        if maxWidth:
            if not maxHeight:
                maxHeight = maxWidth
            self.assertLessEqual(w, maxWidth)
        if maxHeight:
            self.assertLessEqual(h, maxHeight)
        if maxArea:
            self.assertLessEqual(w * h, maxArea)
        return(w, h)

    def test_no_limit(self):
        """Test cases where no constraints are specified."""
        self.assertEqual(self.max(1, 1), (1, 1))
        self.assertEqual(self.max(1234, 12345), (1234, 12345))

    def test_maxArea(self):
        """Test cases for maxArea constraint."""
        self.assertEqual(self.max(1, 1, maxArea=10000), (1, 1))
        self.assertEqual(self.max(100, 100, maxArea=10000), (100, 100))
        self.assertEqual(self.max(101, 101, maxArea=10000), (100, 100))

    def test_maxWidth(self):
        """Test cases for maxWidth constraint."""
        self.assertEqual(self.max(1, 1, maxWidth=123), (1, 1))
        self.assertEqual(self.max(123, 123, maxWidth=123), (123, 123))
        self.assertEqual(self.max(124, 124, maxWidth=123), (123, 123))
        self.assertEqual(self.max(6000, 4000, maxWidth=30), (30, 20))
        self.assertEqual(self.max(30, 4000, maxWidth=30), (0, 30))

    def test_maxWidthHeight(self):
        """Test cases for maxWidth and maxHeight constraints."""
        self.assertEqual(self.max(124, 124, maxWidth=123, maxHeight=124), (123, 123))
        self.assertEqual(self.max(124, 124, maxWidth=123, maxHeight=122), (122, 122))
        self.assertEqual(self.max(6000, 4000, maxWidth=1000, maxHeight=20), (30, 20))
        self.assertEqual(self.max(6010, 4000, maxWidth=1000, maxHeight=20), (30, 20))
        self.assertEqual(self.max(6000, 12, maxWidth=1000, maxHeight=20), (1000, 2))  # exact
        self.assertEqual(self.max(6000, 14, maxWidth=1000, maxHeight=20), (1000, 2))
        self.assertEqual(self.max(6000, 15, maxWidth=1000, maxHeight=20), (1000, 3))
        self.assertEqual(self.max(6000, 18, maxWidth=1000, maxHeight=20), (1000, 3))  # exact

    def test_maxAreaWidthHeight(self):
        """Test cases with combined constraints."""
        self.assertEqual(self.max(110, 110, maxArea=10000, maxWidth=110, maxHeight=110), (100, 100))
        self.assertEqual(self.max(110, 110, maxArea=20000, maxWidth=110, maxHeight=105), (105, 105))
        self.assertEqual(self.max(6000, 1000, maxArea=900000, maxWidth=2000, maxHeight=1000), (2000, 333))
        self.assertEqual(self.max(6000, 30, maxArea=900000, maxWidth=2000, maxHeight=1000), (2000, 10))
        self.assertEqual(self.max(6000, 6000, maxArea=900000, maxWidth=2000, maxHeight=1000), (948, 948))
        self.assertEqual(self.max(4000, 6000, maxArea=900000, maxWidth=2000, maxHeight=1000), (667, 1000))
        self.assertEqual(self.max(60, 6000, maxArea=900000, maxWidth=2000, maxHeight=1000), (10, 1000))
        self.assertEqual(self.max(6000, 6000, maxArea=900, maxWidth=1000, maxHeight=1000), (30, 30))
        self.assertEqual(self.max(6000, 60, maxArea=900, maxWidth=1000, maxHeight=1000), (300, 3))
        self.assertEqual(self.max(6000, 10, maxArea=900, maxWidth=1000, maxHeight=1000), (734, 1))


if __name__ == '__main__':
    unittest.main()
