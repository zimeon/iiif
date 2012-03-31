#!/usr/bin/env python

"""Test encoding and decoding of the request URLs in the i3f spec

For http://library.stanford.edu/iiif/image-api/ v0.1 dated "9 March 2012"

Run as ./i3f_urltest_spec.py

This test includes only test cases for the table in section 7. See
i3f_urltest.py for more examples that test other cases and alternative 
forms which should still be decoded correctly.

Simeon Warner - 2012-03-23
"""
import unittest

from i3f.request import I3fRequest

# Data for test. Format is
# name : [ {args}, 'canonical_url', 'alternate_form1', ... ]
# 
data  = {
    '01_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'color':'color' },
        'id1/full/100,100/0/color'],
    '02_params': [
        {'identifier':'id1', 'region':'full', 'size':'100,100', 'rotation':'0', 'color':'color', 'format':'jpg' },
        'id1/full/100,100/0/color.jpg'],
    '03_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'size':'pct:100', 'rotation':'270', 'color':'grey', 'format':'jpg'},
        'bb157hs6068/full/pct:100/270/grey.jpg'],
# Named profile
    '04_profile': [
        {'identifier':'id1', 'profile':'thumb', },
        'id1/thumb'],
    '05_profile': [
        {'identifier':'id1', 'profile':'thumb', 'format':'png' },
        'id1/thumb.png'],
# ARKs from http://tools.ietf.org/html/draft-kunze-ark-00
# ark:sneezy.dopey.com/12025/654xz321
# ark:/12025/654xz321
    '06_profile': [
        {'identifier':'ark:/12025/654xz321', 'profile':'mobile'},
        'ark:%2F12025%2F654xz321/mobile'],
# URNs from http://tools.ietf.org/html/rfc2141
# urn:foo:a123,456
    '07_profile': [
        {'identifier':'urn:foo:a123,456', 'profile':'mobile'},
        'urn:foo:a123,456/mobile'],
# URNs from http://en.wikipedia.org/wiki/Uniform_resource_name
# urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4
# ** note will get double encoding **
    '08_profile': [
        {'identifier':'urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4', 'profile':'mobile'},
        'urn:sici:1046-8188(199501)13:1%253C69:FTTHBI%253E2.0.TX;2-4/mobile'],
# Extreme silliness
    '09_profile': [
        {'identifier':'http://example.com/?54#a', 'profile':'mobile'},
        'http:%2F%2Fexample.com%2F%3F54%23a/mobile'],
    }

class TestAll(unittest.TestCase):

    def test1_encode(self):
        print "Encoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            print tname + "   " + self.pstr(data[tname][0]) + "  " + data[tname][1]
            i3f = I3fRequest(**data[tname][0])
            self.assertEqual(i3f.url(),data[tname][1])
        print
  
    def test2_decode(self):
        print "Decoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            pstr = self.pstr(data[tname][0])
            for turl in data[tname][1:]:
                i3f = I3fRequest().parse_url(turl)
                tstr = self.pstr(i3f.__dict__)
                print tname + "   " + tstr + " -> " + turl
                self.assertEqual(tstr,pstr)
        print

    def pstr(self,p):
        str=''
        for k in ['identifier','region','size','rotation','color','profile','format']:
            if k in p and p[k]:
                str += k+'='+p[k]+' '
        return(str)
        
# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
