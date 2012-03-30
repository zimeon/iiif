#!/usr/bin/env python
#
# Run simply as ./i3f_urltest.py
# Simeon Warner - 2012-02-14
import unittest

from i3f import *

# Data for test. Format is
# name : [ {args}, 'canonical_url', 'alternate_form1', ... ]
# 
data  = {
    '00_params': [
        {'identifier':'id1', 'region':'all', 'rotation':'0', 'size':'100,100' },
        'id1/all/0/100,100'],
    '01_params': [
        {'identifier':'id1', 'region':'all', 'rotation':'0', 'size':'100,100','format':'jpg' },
        'id1/all/0/100,100.jpg'],
    '02_params': [
        {'identifier':'id1', 'region':'all', 'rotation':'0', 'size':'100,100','quality':'bpp:3.0' },
        'id1/all/0/100,100/bpp%3A3.0',
        'id1/all/0/100,100/bpp:3.0'],
    '03_params': [
        {'identifier':'id1', 'region':'all', 'rotation':'0', 'size':'100,100','quality':'bpp:3.0', 'format':'tif' },
        'id1/all/0/100,100/bpp%3A3.0.tif'],
    '05_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'rotation':'270', 'size':'pct:100', 'format':'jpg'},
        'bb157hs6068/full/270/pct%3A100.jpg'],
    '06_params': [
        {'identifier':'bb157hs6068', 'region':'full', 'rotation':'123.456', 'size':'100,', 'format':'jpg'},
        'bb157hs6068/full/123.456/100,.jpg'],
# Named profile
    '10_profile': [
        {'identifier':'id1', 'profile':'thumb', },
        'id1/thumb'],
    '11_profile': [
        {'identifier':'id1', 'profile':'thumb', 'format':'png' },
        'id1/thumb.png'],
# ARKs from http://tools.ietf.org/html/draft-kunze-ark-00
# ark:sneezy.dopey.com/12025/654xz321
# ark:/12025/654xz321
    '21_ARK ': [
        {'identifier':'ark:sneezy.dopey.com/12025/654xz321', 'profile':'mobile'},
        'ark%3Asneezy.dopey.com%2F12025%2F654xz321/mobile'],
    '22_ARK ': [
        {'identifier':'ark:/12025/654xz321', 'profile':'mobile'},
        'ark%3A%2F12025%2F654xz321/mobile',
        'ark:%2F12025%2F654xz321/mobile'],
# URNs from http://tools.ietf.org/html/rfc2141
# urn:foo:a123,456
    '31_URN ': [
        {'identifier':'urn:foo:a123,456', 'profile':'mobile'},
        'urn%3Afoo%3Aa123,456/mobile'],
# URNs from http://en.wikipedia.org/wiki/Uniform_resource_name
# urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4
# ** note will get double encoding **
    '32_URN ': [
        {'identifier':'urn:sici:1046-8188(199501)13:1%3C69:FTTHBI%3E2.0.TX;2-4', 'profile':'mobile'},
        'urn%3Asici%3A1046-8188(199501)13%3A1%253C69%3AFTTHBI%253E2.0.TX;2-4/mobile'],
# Extreme silliness
    '41_odd ': [
        {'identifier':'http://example.com/?54#a', 'profile':'mobile'},
        'http%3A%2F%2Fexample.com%2F%3F54%23a/mobile',
        'http:%2F%2Fexample.com%2F?54#a/mobile'],

    }

class TestAll(unittest.TestCase):

    def test1_encode(self):
        print "Encoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            print tname + "   " + self.pstr(data[tname][0]) + "  " + data[tname][1]
            i3f = I3f(**data[tname][0])
            self.assertEqual(i3f.url(),data[tname][1])
        print
  
    def test2_decode(self):
        print "Decoding tests..."
        for tname in sorted(data.iterkeys()):
            tdata=data[tname]
            pstr = self.pstr(data[tname][0])
            for turl in data[tname][1:]:
                i3f = I3f().parseurl(turl)
                tstr = self.pstr(i3f.__dict__)
                print tname + "   " + turl + " -> " + tstr
                self.assertEqual(tstr,pstr)
        print

    def test3_decode_except(self):
        #try:
        #    print i.parseurl("id1/all/270/!pct%3A75.23.jpg")
        #except Exception as e:
        #    print "Exception: " + str(e)
        return

    def pstr(self,p):
        str=''
        for k in ['identifier','region','rotation','size','quality','profile','format']:
            if k in p and p[k]:
                str += k+'='+p[k]+' '
        return(str)

        
# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
