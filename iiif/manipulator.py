"""Base/null IIIF image manipulator.

Provides a number of utility methods to extract information necessary
for doing the transformations once one has knowledge of the source
image size.
"""

import logging
import os
import os.path
import re
import shutil
import subprocess

from .error import IIIFError, IIIFZeroSizeError
from .request import IIIFRequest


class IIIFManipulator(object):
    """Manipulate an image according to IIIF rules.

    All exceptions are raise as IIIFError objects which directly
    determine the HTTP response.
    """

    def __init__(self, api_version='2.1'):
        """Initialize Manipulator object.

        Accepts api_version as a parameter to tailor handling of
        requests according to the API being supported.

        Sets compliance_level to None because the null manipulator
        doesn't comply with any level. Sub-classes are expected to
        set this to a level number (0,1,2) appropriate to the
        facilities supported at the given API version. Use
        compliance_uri to get a URI.
        """
        self.api_version = api_version
        self.compliance_level = None
        self.max_area = None
        self.max_width = None
        self.max_height = None
        self.srcfile = None
        self.request = None
        self.outfile = None
        self.logger = logging.getLogger(__name__)

    @property
    def compliance_uri(self):
        """Compliance URI based on api_version.

        Value is based on api_version and complicance_level, will be
        None if either are unset/unrecognized. The assumption here is
        that the api_version and level are orthogonal, override this
        method if that isn't true.
        """
        if (self.api_version == '1.0'):
            uri_pattern = r'http://library.stanford.edu/iiif/image-api/compliance.html#level%d'
        elif (self.api_version == '1.1'):
            uri_pattern = r'http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level%d'
        elif (self.api_version == '2.0' or
              self.api_version == '2.1'):
            uri_pattern = r'http://iiif.io/api/image/2/level%d.json'
        elif (self.api_version == '3.0'):
            uri_pattern = r'http://iiif.io/api/image/3/level%d.json'
        else:
            return
        if (self.compliance_level is None):
            return
        return(uri_pattern % self.compliance_level)

    def derive(self, srcfile=None, request=None, outfile=None):
        """Do sequence of manipulations for IIIF to derive output image.

        Named argments:
        srcfile -- source image file
        request -- IIIFRequest object with parsed parameters
        outfile -- output image file. If set the the output file will be
                   written to that file, otherwise a new temporary file
                   will be created and outfile set to its location.

        See order in spec: http://www-sul.stanford.edu/iiif/image-api/#order

          Region THEN Size THEN Rotation THEN Quality THEN Format

        Typical use:

            r = IIIFRequest(region=...)
            m = IIIFManipulator()
            try:
                m.derive(srcfile='a.jpg',request=r)
                # .. serve m.outfile
            except IIIFError as e:
                # ..
            finally:
                m.cleanup() #removes temp m.outfile
        """
        # set if specified
        if (srcfile is not None):
            self.srcfile = srcfile
        if (request is not None):
            self.request = request
        if (outfile is not None):
            self.outfile = outfile
        if (self.outfile is not None):
            # create path to output dir if necessary
            dir = os.path.dirname(self.outfile)
            if (not os.path.exists(dir)):
                os.makedirs(dir)
        #
        self.do_first()
        (x, y, w, h) = self.region_to_apply()
        self.do_region(x, y, w, h)
        (w, h) = self.size_to_apply()
        self.do_size(w, h)
        (mirror, rot) = self.rotation_to_apply(no_mirror=True)
        self.do_rotation(mirror, rot)
        (quality) = self.quality_to_apply()
        self.do_quality(quality)
        self.do_format(self.request.format)
        self.do_last()
        return(self.outfile, self.mime_type)

    def do_first(self):
        """Simplest possible manipulator that can only handle no modification.

        Set width and height to -1 (unknown).
        """
        self.width = -1  # don't know width of height
        self.height = -1

    def do_region(self, x, y, w, h):
        """Null implementation of region selection."""
        if (x is not None):
            raise IIIFError(code=501, parameter="region",
                            text="Null manipulator supports only region=/full/.")

    def do_size(self, w, h):
        """Null implementation of size scaling."""
        if (w is not None):
            raise IIIFError(code=501, parameter="size",
                            text="Null manipulator supports only size=pct:100 and size=full.")

    def do_rotation(self, mirror, rot):
        """Null implementation of rotate and/or mirror."""
        if (mirror):
            raise IIIFError(code=501, parameter="rotation",
                            text="Null manipulator does not support mirroring.")
        if (rot != 0.0):
            raise IIIFError(code=501, parameter="rotation",
                            text="Null manipulator supports only rotation=(0|360).")

    def do_quality(self, quality):
        """Null implementation of quality."""
        if (self.api_version >= '2.0'):
            if (quality != "default"):
                raise IIIFError(code=501, parameter="default",
                                text="Null manipulator supports only quality=default.")
        else:  # versions 1.0 and 1.1
            if (quality != "native"):
                raise IIIFError(code=501, parameter="native",
                                text="Null manipulator supports only quality=native.")

    def do_format(self, format):
        """Null implementation of format selection.

        This is the last step, this null implementation does not accept any
        specification of a format because we don't even know what the input
        format is.
        """
        if (format is not None):
            raise IIIFError(code=415, parameter="format",
                            text="Null manipulator does not support specification of output format.")
        #
        if (self.outfile is None):
            self.outfile = self.srcfile
        else:
            try:
                shutil.copyfile(self.srcfile, self.outfile)
            except IOError as e:
                raise IIIFError(code=500,
                                text="Failed to copy file (%s)." % (str(e)))
        self.mime_type = None

    def do_last(self):
        """Null implementation of hook in pipeline at end of processing.

        Does nothing.
        """
        return

    # Utility methods

    def region_to_apply(self):
        """Return the x,y,w,h parameters to extract given image width and height.

        Assume image width and height are available in self.width and
        self.height, and self.request is IIIFRequest object

        Expected use:
          (x,y,w,h) = self.region_to_apply()
          if (x is None):
              # full image
          else:
              # extract

        Returns (None,None,None,None) if no extraction is required.
        """
        if (self.request.region_full or
            (self.request.region_pct and
             self.request.region_xywh == (0, 0, 100, 100))):
            return(None, None, None, None)
        # Cannot do anything else unless we know size (in self.width and
        # self.height)
        if (self.width <= 0 or self.height <= 0):
            raise IIIFError(code=501, parameter='region',
                            text="Region parameters require knowledge of image size which is not implemented.")
        if (self.request.region_square):
            if (self.width <= self.height):
                y_offset = (self.height - self.width) / 2
                return(0, y_offset, self.width, self.width)
            else:  # self.width>self.height
                x_offset = (self.width - self.height) / 2
                return(x_offset, 0, self.height, self.height)
        # pct or explicit pixel sizes
        pct = self.request.region_pct
        (x, y, w, h) = self.request.region_xywh
        # Convert pct to pixels based on actual size
        if (pct):
            x = int((x / 100.0) * self.width + 0.5)
            y = int((y / 100.0) * self.height + 0.5)
            w = int((w / 100.0) * self.width + 0.5)
            h = int((h / 100.0) * self.height + 0.5)
        # Check if boundary extends beyond image and truncate
        if ((x + w) > self.width):
            w = self.width - x
        if ((y + h) > self.height):
            h = self.height - y
        # Final check to see if we have the whole image
        if (w == 0 or h == 0):
            raise IIIFZeroSizeError(code=400, parameter='region',
                                    text="Region parameters would result in zero size result image.")
        if (x == 0 and y == 0 and w == self.width and h == self.height):
            return(None, None, None, None)
        return(x, y, w, h)

    def size_to_apply(self):
        """Calculate size of image scaled using size parameters.

        Assumes current image width and height are available in self.width and
        self.height, and self.request is IIIFRequest object.

        Formats are: w, ,h w,h pct:p !w,h full max ^w, ^,h ^w,h

        Returns (None,None) if no scaling is required.

        If max is requested and neither max_area or max_width are
        specified then this is the same as full. Otherwise the limits
        are used to determine the size.
        """
        if (self.request.size_full or self.request.size_pct == 100.0):
            # full size
            return(None, None)
        # Not trivially full size, look at possibilities in turn
        w = self.width
        h = self.height
        if (self.request.size_max):
            # use size limits if present, else full
            if (self.max_area and self.max_area < (w * h)):
                scale = (float(self.max_area) / float(w * h)) ** 0.5
                w = int(w * scale + 0.5)
                h = int(h * scale + 0.5)
            if (self.max_width):
                max_height = self.max_height if self.max_height is not None else self.max_width
                if (self.max_width < w):
                    # calculate wrt original width, height rather than
                    # w, h to avoid compounding rounding issues
                    scale = float(self.max_width) / float(self.width)
                    w = int(self.width * scale + 0.5)
                    h = int(self.height * scale + 0.5)
                if (max_height < h):
                    scale = float(max_height) / float(self.height)
                    w = int(self.width * scale + 0.5)
                    h = int(self.height * scale + 0.5)
        elif (self.request.size_pct is not None):
            w = int(self.width * self.request.size_pct / 100.0 + 0.5)
            h = int(self.height * self.request.size_pct / 100.0 + 0.5)
        elif (self.request.size_bang):
            # Have "!w,h" form
            (mw, mh) = self.request.size_wh
            # Pick smaller fraction and then work from that...
            frac = min((float(mw) / float(self.width)),
                       (float(mh) / float(self.height)))
            w = int(self.width * frac + 0.5)
            h = int(self.height * frac + 0.5)
        else:
            # Must now be "w,h", "w," or ",h". If both are specified then this will the size,
            # otherwise find other to keep aspect ratio
            (w, h) = self.request.size_wh
            if (w is None):
                w = int(self.width * h / self.height + 0.5)
            elif (h is None):
                h = int(self.height * w / self.width + 0.5)
        # Now have w,h, sanity check and return
        if (w == 0 or h == 0):
            raise IIIFZeroSizeError(
                code=400, parameter='size',
                text="Size parameter would result in zero size result image (%d,%d)." % (w, h))
        # Below would be test for scaling up image size, this is allowed by spec
        if ((w > self.width or h > self.height) and self.api_version >= '3.0' and not self.request.size_caret):
            raise IIIFError(code=400, parameter='size',
                            text="Size requests scaling up image to larger than orginal.")
        if (w == self.width and h == self.height):
            return(None, None)
        return(w, h)

    def rotation_to_apply(self, only90s=False, no_mirror=False):
        """Check and interpret rotation.

        Returns a truth value as to whether to mirror, and a floating point
        number 0 <= angle < 360 (degrees).
        """
        rotation = self.request.rotation_deg
        if (no_mirror and self.request.rotation_mirror):
            raise IIIFError(code=501, parameter="rotation",
                            text="This implementation does not support mirroring.")
        if (only90s and (rotation != 0.0 and rotation != 90.0 and
                         rotation != 180.0 and rotation != 270.0)):
            raise IIIFError(code=501, parameter="rotation",
                            text="This implementation supports only 0,90,180,270 degree rotations.")
        return(self.request.rotation_mirror, rotation)

    def quality_to_apply(self):
        """Value of quality parameter to use in processing request.

        Simple substitution of 'native' or 'default' if no quality
        parameter is specified.
        """
        if (self.request.quality is None):
            if (self.api_version <= '1.1'):
                return('native')
            else:
                return('default')
        return(self.request.quality)

    def cleanup(self):
        """Null implementation of clean up after derive call and use of output.

        Call after any output file from the derivation process has been
        read. Intended to handle any clean up of temporary files or such.
        This method empty in base class.
        """
        pass

    def scale_factors(self, tile_width, tile_height=None):
        """Return a set of scale factors for given tile and window size.

        Gives a set of scale factors, starting at 1, and in multiples
        of 2. Largest scale_factor is so that one tile will cover the
        entire image (self.width,self.height).

        If tile_height is not specified then tiles are assumed to be
        squares of tile_width pixels.
        """
        if (not tile_height):
            tile_height = tile_width
        sf = 1
        scale_factors = [sf]
        for j in range(30):  # limit of 2^30, should be enough!
            sf = 2 * sf
            if (tile_width * sf > self.width and
                    tile_height * sf > self.height):
                break
            scale_factors.append(sf)
        return scale_factors
