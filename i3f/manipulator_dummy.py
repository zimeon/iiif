"""Null implementation i3f image manipulation"""

import re
import os
import os.path
import subprocess

from error import I3fError
from request import I3fRequest
from manipulator import I3fManipulator

class I3fManipulatorDummy(I3fManipulator):
    """Module implements only manipulations that specify no change

    All exceptions are raise as I3fError objects which directly
    determine the HTTP response.
    """

    def __init__(self):
        """Return URI indicating i3f compliance level, or None if not

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
        # Region
        (x,y,w,h)=self.region_to_apply()
        if (x is not None):
            raise I3fError(code=501,parameter="region",
                           text="Dummy manipulator supports only region=/full/.")

    def do_size(self):
        # Size
        # (w,h) = self.size_to_apply()
        if (self.i3f.size_pct != 100.0):
            raise I3fError(code=501,parameter="size",
                           text="Dummy manipulator supports only size=pct:100.")

    def do_rotation(self):
        # Rotate
        if (self.rotation_to_apply() != 0.0):
            raise I3fError(code=501,parameter="rotation",
                           text="Dummy manipulator supports only rotation=(0|360).")

    def do_color(self):
        # Color
        if (self.color_to_apply() != 'color'):
            raise I3fError(code=501,parameter="color",
                           text="Dummy manipulator supports only color=color.")

    def do_format(self):
        if (self.i3f.format is not None):
            raise I3fError(code=415,parameter="format",
                           text="Dummy manipulator does not support specification of output format.")
        self.outfile=self.srcfile
        self.mime_type=None

    def do_last(self):
        # Nothing
        return
