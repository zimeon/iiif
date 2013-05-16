"""Implementation of i3f image manipulations using the Python Image Library (PIL)

Uses the Python Image Library (PIL) for in-python manipulation:
http://www.pythonware.com/products/pil/index.htm
"""

import re
import os
import os.path
import subprocess

from PIL import Image

from error import I3fError
from request import I3fRequest
from manipulator import I3fManipulator

class I3fManipulatorPIL(I3fManipulator):
    """Module to manipulate and image according to i3f rules

    All exceptions are raise as Error objects which directly
    determine the HTTP response.
    """

    tmpdir = '/tmp'
    filecmd = None
    pnmdir = None

    def __init__(self):
        super(I3fManipulatorPIL, self).__init__()
        # Does not support jp2 output
        self.complianceLevel="http://i3f.example.org/compliance/level/0"

    def do_first(self):
        """Create PIL object from input
        """
        try:
            self.image=Image.open(self.srcfile)
            self.image.load()
        except Exception as e:
            raise Error(text="PIL Image.open(..) barfed: "+str(e))
        #
        (self.width,self.height)=self.image.size

    def do_region(self):
        (x,y,w,h)=self.region_to_apply()
        if (x is None):
            print "region: full (nop)"
        else:
            print "region: (%d,%d,%d,%d)" % (x,y,w,h)
            self.image = self.image.crop( (x,y,x+w,y+h) )
            self.width = w
            self.height = h

    def do_size(self):
        (w,h)=self.size_to_apply()
        if (w is None):
            print "size: no scaling (nop)"
        else:
            print "size: scaling to (%d,%d)" % (w,h)
            self.image = self.image.resize( (w,h) )
            self.width = w
            self.height = h

    def do_rotation(self):
        rot=self.rotation_to_apply()
        if (rot==0.0):
            print "rotation: no rotation (nop)"
        else:
            print "rotation: by %f degrees clockwise" % (rot)
            self.image = self.image.rotate( -rot, expand=True )

    def do_quality(self):
        quality=self.quality_to_apply()
        if (quality == 'grep'):
            print "quality: grey"
        elif (quality == 'bitonal'):
            print "quality: bitonal"
        else: 
            print "quality: quality (nop)"

    def do_format(self):
        fmt = ( 'png' if (self.i3f.format is None) else self.i3f.format)
        if (fmt == 'png'):
            print "format: png"
            self.outfile='/tmp/pil.png'
            self.image.save(self.outfile)
            self.mime_type="image/png"
            self.output_format=fmt
        else:
            raise Error(code=415, parameter='format',
                        text="Unsupported output file format (%s), only png,jpg,tiff are supported."%(fmt))

