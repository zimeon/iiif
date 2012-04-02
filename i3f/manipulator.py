""" Almost null implementation i3f image manipulations and base class 

Provides a number of utility methods to extract information necessary
for doing the transformations once one has knowledge of the source
image size.
"""

import re
import os
import os.path
import subprocess

from error import I3fError
from request import I3fRequest

class I3fManipulator(object):
    """ Manipulate an image according to IIIF rules

    All exceptions are raise as I3fError objects which directly
    determine the HTTP response.
    """

    def __init__(self):
        """ Return URI indicating IIIF compliance level, or None if not

        The attribute complicanceLevel is set of either None or a URI 
        that can be used in the HTTP response headers like of the form

        Link: <http://i3f.example.org/compliance/level/0>;rel="compliesTo"

        This dummy manipulator doesn't comply to any of the levels defined
        in the i3f specification so it is set to None.
        """
        self.file = None;
        self.source = None;
        self.complianceLevel = None;

    def do_i3f_manipulation(self,file=None,i3f=None):
        """ Do sequence of manipulations for IIIF

        Calls methods in sequence: do_first -> do_region -> do_size ->
        do_rotation -> do_color -> do_format -> do_last
        """
        self.srcfile=file
        self.i3f=i3f
        self.do_first()
        self.do_region()
        self.do_size()
        self.do_rotation()
        self.do_color()
        self.do_format()
        self.do_last()
        return(self.outfile,self.mime_type)

    def do_first(self):
        """Simplest possible manipulator that can only handle no modification

        Parse out the request and respond with an error unless it
        specified an unmodified image. Returns None for the mime type.
        """
        self.width=-1  #don't know width of height
        self.height=-1 

    def do_region(self):
        """ Extract specified region in manipulation pipeline
        """
        (x,y,w,h)=self.region_to_apply()
        if (x is not None):
            raise I3fError(code=501,parameter="region",
                           text="Dummy manipulator supports only region=/full/.")

    def do_size(self):
        """ Scale extracted region in manipulation pipeline
        """
        if (size.i3f.size_pct is None or self.i3f.size_pct != 100.0):
            raise I3fError(code=501,parameter="size",
                           text="Dummy manipulator supports only size=pct:100.")

    def do_rotation(self):
        """ Rotate extracted/scaled region in manipulation pipeline
        """
        if (self.i3f.rotation_to_apply() != 0.0):
            raise I3fError(code=501,parameter="rotation",
                           text="Dummy manipulator supports only rotation=(0|360).")

    def do_color(self):
        """ Change bit-depth in manipulation pipeline
        """
        if (self.i3f.color_to_apply() != 'color'):
            raise I3fError(code=501,parameter="color",
                           text="Dummy manipulator supports only color=color.")

    def do_format(self):
        """ Change format of result from manipulation pipeline
        """
        if (self.i3f.format is not None):
            raise I3fError(code=415,parameter="format",
                           text="Dummy manipulator does not support specification of output format.")
        self.outfile=self.srcfile
        self.mime_type=None

    def do_last(self):
        """ Hook in pipeline at end of processing
        """
        return

    def region_to_apply(self):
        """Return the x,y,w,h parameters to extract given image width and height

        Assume image width and height are available in self.width and 
        self.height, and self.i3f is I3fRequest object 

        Expected use:
          (x,y,w,h) = self.region_to_apply()
          if (x is None):
              # full image
          else:
              # extract
        Returns (None,None,None,None) if no extraction is required.
        """
        if (self.i3f.region_full):
            return(None,None,None,None)
        pct = self.i3f.region_pct
        (x,y,w,h)=self.i3f.region_xywh
        # Convert pct to real
        if (pct):
            x = int( (x / 100.0) * self.width + 0.5)
            y = int( (y / 100.0) * self.height + 0.5)
            w = int( (w / 100.0) * self.width + 0.5)
            h = int( (h / 100.0) * self.height + 0.5)
        # Check if boundary extends beyond image and truncate
        if ((x+w) > self.width):
            w=self.width-x
        if ((y+h) > self.height):
            h=self.height-y
        # Final check to see if we have the whole image
        if ( w==0 or h==0 ):
            raise I3fError(code=400,parameter='region',
                           text="Region parameters would result in zero size result image.")
        if ( x==0 and y==0 and w==self.width and h==self.height ):
            return(None,None,None,None)
        return(x,y,w,h)

    def size_to_apply(self):
        """Calculate size of image scaled using size parameters

        Assumes current image width and height are available in self.width and 
        self.height, and self.i3f is I3fRequest object 

        Formats are: w, ,h w,h pct:p !w,h

        Expected use:
          (w,h) = self.size_to_apply(region_w,region_h)
          if (q is None):
              # full image
          else:
              # scale to w by h
        Returns (None,None) if no scaling is required.
        """
        if (self.i3f.size_pct is not None):
            w = int(self.width * self.i3f.size_pct / 100.0 + 0.5)
            h = int(self.height * self.i3f.size_pct / 100.0 + 0.5)
        elif (self.i3f.size_bang):
            # Have "!w,h" form
            (mw,mh)=self.i3f.size_wh
            # Pick smaller fraction and then work from that...
            frac = min ( (float(mw)/float(self.width)), (float(mh)/float(self.height)) )
            #print "size=!w,h: mw=%d mh=%d -> frac=%f" % (mw,mh,frac)
            # FIXME - could put in some other function here like factors of two, but
            # FIXME - for now just pick largest image within requested dimensions
            w = int(self.width * frac + 0.5)
            h = int(self.height * frac + 0.5)
        else:
            # Must now be "w,h", "w," or ",h". If both are specified then this will the size,
            # otherwise find other to keep aspect ratio
            (w,h)=self.i3f.size_wh
            if (w is None):
                w = int(self.width * h / self.height + 0.5)
            elif (h is None):
                h = int(self.height * w / self.width + 0.5)
            #print "size=w,h: w=%d h=%d" % (w,h)
        # Now have w,h, sanity check and return
        if ( w==0 or h==0 ):
            raise I3fError(code=400,parameter='size',
                           text="Size parameter would result in zero size result image (%d,%d)."%(w,h))
# FIXME - this isn't actually forbidden by v0.1 of the spec
#        if ( w>self.width or h>self.height ):
#            raise I3fError(code=400,parameter='size',
#                           text="Size requests scaling up image to larger than orginal.")
        if ( w==self.width and h==self.height ):    
            return(None,None)
        return(w,h)

    def rotation_to_apply(self, only90s=False):
        """Check an interpret rotation

        Returns a floating point number 0 <= angle < 360 (degrees).
        """
        rotation=self.i3f.rotation_deg
        if (only90s and (rotation!=0.0 and rotation!=90.0 and 
                         rotation!=180.0 and rotation!=270.0)):
            raise I3fError(code=501,parameter="rotation",
                           text="This implementation supports only 0,90,180,270 degree rotations.")
        return(rotation)

    def color_to_apply(self):
        """Value of color parameter to use in processing request

        Simple substitution of 'color' for default.
        """
        if (self.i3f.color is None):
            return('color')
        return(self.i3f.color)

    def cleanup(self):
        """Clean up after manipulation

        Call after any output file from the manipulation process has been read. Intended
        to handle any clean up of temporary files or such. This method empty.
        """
        return()
