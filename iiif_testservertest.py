#!/usr/bin/env python

"""Test the testserver...

"""
import unittest
from urllib2 import *

baseurl='http://localhost:8000/pil/'

class TestAll(unittest.TestCase):

    def get(self,path):
        print "get("+path+")..."
        try:
            f = urlopen(baseurl+path)
            img_size = 0
            while (1):
                buffer = f.read(8192)
                if (not buffer):
                    break
                img_size+=len(buffer)
            return(img_size)
        except HTTPError as e:
            return('code'+str(e.code))
        except Exception as e:
            return('other_error_'+str(e))
        
    def test1_success(self):
        print "Success tests..."
        id = "214-2.png"
        size = 13929
        self.assertEqual( self.get(id+'/full/pct:100/0/color'), size)
        self.assertEqual( self.get(id+'/full/pct:100/360/color'), size)
        self.assertEqual( self.get(id+'/full/pct:100.000/0/color'), size)
        self.assertEqual( self.get(id+'/full/pct:100/0.0/color'), size)
        self.assertEqual( self.get(id+'/full/pct:100/.000/color'), size)
        self.assertEqual( self.get(id+'/full/pct:100/0/color.png'), size)
        self.assertEqual( self.get(id+'/full/pct:99.99/0/color'), size)
        #self.assertEqual( self.get('/214-2.png/0,0,50,100/pct:100/360/color.png'), 0 )

    def test2_errors(self):
        print "Error tests..."
        id = "214-2.png"
        # Numbers of params
        self.assertEqual( self.get('1param'), 'code400' )
        self.assertEqual( self.get('1param/2/3'), 'code400' )
        self.assertEqual( self.get('1param/2/3/4'), 'code400' )
        self.assertEqual( self.get('1param/2/3/4/5/6'), 'code400' )
        self.assertEqual( self.get('1param/2/3/4/5/6/7'), 'code400' )
        # Simple bogus params
        self.assertEqual( self.get('bad-id/full/pct:100/0/color'), 'code404' )
        self.assertEqual( self.get(id+'/bogus-profile'), 'code400' )
        self.assertEqual( self.get(id+'/bogus-profile.png'), 'code400' )
        # Bad region
        self.assertEqual( self.get(id+'//pct:100/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/whole/pct:100/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/0,0,0,0/pct:100/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/100,0,100,100/pct:100/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/0,100,100,100/pct:100/0/color'), 'code400' )        
        # Bad size
        self.assertEqual( self.get(id+'/full/pct:101/0/color'), 14024 )        
        self.assertEqual( self.get(id+'/full/pct:0/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/pct:0.1/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/pct:100.1/0/color'), 13929 )        
        self.assertEqual( self.get(id+'/full/0,0/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/0,/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/,0/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/,/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/101,/0/color'), 14024 )        
        self.assertEqual( self.get(id+'/full/,101/0/color'), 14024 )        
        self.assertEqual( self.get(id+'/full/1.0,1.0/0/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/1.1,1.1/0/color'), 'code400' )        
        # Bad rotation
        self.assertEqual( self.get(id+'/full/full/-1/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/full/-0.001/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/full/361/color'), 'code400' )        
        self.assertEqual( self.get(id+'/full/full/360.1/color'), 'code400' )        
        # Bad color
        self.assertEqual( self.get(id+'/full/pct:100/0/bogus'), 'code400' )        
        # Bad format
        ##self.assertEqual( self.get(id+'/full/pct:100/0/color.'), 'code415' )        
        self.assertEqual( self.get(id+'/full/pct:100/0/color.FMT'), 'code415' )        

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
