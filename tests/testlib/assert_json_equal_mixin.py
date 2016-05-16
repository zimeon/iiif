"""Provide assertJSONEqual test for use with unittest."""
import re


class AssertJSONEqual(object):
    """Mixin for unitest.TestCase provding assertJSONEqual()."""

    def assertJSONEqual(self, stra, strb):
        """Check JSON strings for equality.

        In python2.x the as_json method includes spaces after commas
        but before newline, this is not included in python3.x. Strip such
        spaces before doing the comparison.
        """
        a = re.sub(r',\s+', ',', stra)
        b = re.sub(r',\s+', ',', strb)
        self.assertEqual(a, b)
