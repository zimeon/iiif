"""
Implementation of IIIF Image API manipulations using the Python Image Library

Uses the Python Image Library (PIL) for in-python manipulation:
http://www.pythonware.com/products/pil/index.htm
"""

import re
import os
import os.path
import subprocess
import tempfile

from PIL import Image

from error import IIIFError
from request import IIIFRequest
from manipulator import IIIFManipulator

class IIIFManipulatorPIL(IIIFManipulator):
    """Module to manipulate and image according to iiif rules

    All exceptions are raise as Error objects which directly
    determine the HTTP response.
    """

    tmpdir = '/tmp'
    filecmd = None
    pnmdir = None

    def __init__(self, **kwargs):
        super(IIIFManipulatorPIL, self).__init__(**kwargs)
        # Does not support jp2 output
        self.complianceLevel="http://iiif.example.org/compliance/level/0"
        self.outtmp = None

    def do_first(self):
        """Create PIL object from input image file
        """
        self.logger.info("do_first: src=%s" % (self.srcfile))
        try:
            self.image=Image.open(self.srcfile)
            self.image.load()
        except Exception as e:
            raise IIIFError(text=("PIL Image.open(%s) barfed: %s",(self.srcfile,str(e))))
        (self.width,self.height)=self.image.size

    def do_region(self):
        (x,y,w,h)=self.region_to_apply()
        if (x is None):
            self.logger.info("region: full (nop)")
        else:
            self.logger.info("region: (%d,%d,%d,%d)" % (x,y,w,h))
            self.image = self.image.crop( (x,y,x+w,y+h) )
            self.width = w
            self.height = h

    def do_size(self):
        (w,h)=self.size_to_apply()
        if (w is None):
            self.logger.info("size: no scaling (nop)")
        else:
            self.logger.info("size: scaling to (%d,%d)" % (w,h))
            self.image = self.image.resize( (w,h) )
            self.width = w
            self.height = h

    def do_rotation(self):
        (mirror,rot)=self.rotation_to_apply()
        if (not mirror and rot==0.0):
            self.logger.info("rotation: no rotation (nop)")
        else:
            #FIXME - with PIL one can use the transpose() method to do 90deg
            #FIXME - rotations as well as mirroring. This would be more efficient
            #FIXME - for these cases than mirror _then_ rotate.
            if (mirror):
                self.logger.info("rotation: mirror (about vertical axis)")
                self.image = self.image.transpose( Image.FLIP_LEFT_RIGHT )
            if (rot!=0.0):
                self.logger.info("rotation: by %f degrees clockwise" % (rot))
                self.image = self.image.rotate( -rot, expand=True )

    def do_quality(self):
        """Apply value of quality parameter

        For PIL docs see 
        <http://pillow.readthedocs.org/en/latest/reference/Image.html#PIL.Image.Image.convert>
        """
        quality=self.quality_to_apply()
        if (quality == 'grey' or quality == 'gray'):
            # Checking for 1.1 gray or 20.0 grey elsewhere
            self.logger.info("quality: converting to gray")
            self.image = self.image.convert('L')
        elif (quality == 'bitonal'):
            self.logger.info("quality: converting to bitonal")
            self.image = self.image.convert('1')
        else:
            self.logger.info("quality: quality (nop)")

    def do_format(self):
        # assume tiling apps want jpg...
        fmt = ( 'jpg' if (self.request.format is None) else self.request.format)
        if (fmt == 'png'):
            self.logger.info("format: png")
            self.mime_type="image/png"
            self.output_format=fmt
            format = 'png'
        elif (fmt == 'jpg'):
            self.logger.info("format: jpg")
            self.mime_type="image/jpeg"
            self.output_format=fmt
            format = 'jpeg';
        else:
            raise IIIFError(code=415, parameter='format',
                            text="Unsupported output file format (%s), only png,jpg are supported."%(fmt))

        if (self.outfile is None):
            # Create temp
            f = tempfile.NamedTemporaryFile(delete=False)
            self.outfile=f.name
            self.outtmp=f.name
            self.image.save(f,format=format)
        else:
            # Save to specified location
            self.image.save(self.outfile,format=format)

    def cleanup(self):
        if (self.outtmp is not None):
            try:
                os.unlink(self.outtmp)
            except OSError as e:
                # FIXME - should log warning when we have logging...
                pass
