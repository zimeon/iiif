"""Shared code for test_request_*.

Simeon Warner, 2016-05...
"""
import unittest
from iiif.request import IIIFRequest


class TestRequests(unittest.TestCase):
    """Version of TestCase with extras."""

    def check_encoding(self, data, api_version):
        """Encoding.

        Checks that every for each test in the dict data,
        the data values (first element) encode to the URL
        given (second element).
        """
        for tname in sorted(data.keys()):
            tdata = data[tname]
            iiif = IIIFRequest(api_version=api_version, **data[tname][0])
            self.assertEqual(iiif.url(), data[tname][1])

    def check_decoding(self, data, api_version):
        """Decoding.

        Reverse of check_encoding(). Checks that for each test
        the URL (second element) is decoded to the given data
        values (first element).
        """
        for tname in sorted(data.keys()):
            tdata = data[tname]
            pstr = self._pstr(data[tname][0])
            for turl in data[tname][1:]:
                iiif = IIIFRequest(api_version).split_url(turl)
                tstr = self._pstr(iiif.__dict__)
                self.assertEqual(tstr, pstr)

    def _pstr(self, p):
        """Create string for request values.

        Does this in the same way that it is done in the Image
        API spec.
        """
        s = ''
        for k in ['identifier', 'region', 'size', 'rotation',
                  'default', 'info', 'format']:
            if k in p and p[k]:
                s += k + '=' + str(p[k]) + ' '
        return(s)
