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
        def normalize(json_str):
            s = re.sub(r'\s*,\s+', ',\n', json_str)
            s = re.sub(r'\s+$', '', s)
            return s
        self.maxDiff = None
        self.assertEqual(normalize(stra), normalize(strb))
