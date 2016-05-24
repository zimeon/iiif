"""Implementation of IIIF Image API manipulations using the Python Image Library.

Uses the Python Image Library (PIL) for in-python manipulation:
http://www.pythonware.com/products/pil/index.htm
"""

import re
import os
import os.path
import subprocess
import tempfile

from PIL import Image

from .error import IIIFError
from .request import IIIFRequest
from .manipulator import IIIFManipulator


class IIIFManipulatorPIL(IIIFManipulator):
    """Class to manipulate an image with PIL according to IIIF.

    All exceptions are raised as IIIFError objects which directly
    determine the HTTP response.
    """

    tmpdir = '/tmp'
    filecmd = None
    pnmdir = None

    def __init__(self, **kwargs):
        """Initialize IIIFManipulatorPIL object.

        Keyword arguments are passes to superclass initialize method.
        """
        super(IIIFManipulatorPIL, self).__init__(**kwargs)
        # Does not support jp2 output
        self.compliance_level = 2
        self.outtmp = None

    def set_max_image_pixels(self, pixels):
        """Set PIL limit on pixel size of images to load if non-zero.

        WARNING: This is a global setting in PIL, it is
        not local to this manipulator instance!

        Setting a value here will not only set the given limit but
        also convert the PIL "DecompressionBombWarning" into an
        error. Thus setting a moderate limit sets a hard limit on
        image size loaded, setting a very large limit will have the
        effect of disabling the warning.
        """
        if (pixels):
            Image.MAX_IMAGE_PIXELS = pixels
            Image.warnings.simplefilter(
                'error', Image.DecompressionBombWarning)

    def do_first(self):
        """Create PIL object from input image file.

        Image location must be in self.srcfile. Will result in
        self.width and self.height being set to the image dimensions.

        Will raise an IIIFError on failure to load the image
        """
        self.logger.debug("do_first: src=%s" % (self.srcfile))
        try:
            self.image = Image.open(self.srcfile)
        except Image.DecompressionBombWarning as e:
            # This exception will be raised only if PIL has been
            # configured to raise an error in the case of images
            # that exceeed Image.MAX_IMAGE_PIXELS, with
            # Image.warnings.simplefilter('error', Image.DecompressionBombWarning)
            raise IIIFError(text=("Image size limit exceeded (PIL: %s)" % (str(e))))
        except Exception as e:
            raise IIIFError(text=("Failed to read image (PIL: %s)" % (str(e))))
        (self.width, self.height) = self.image.size

    def do_region(self, x, y, w, h):
        """Apply region selection."""
        if (x is None):
            self.logger.debug("region: full (nop)")
        else:
            self.logger.debug("region: (%d,%d,%d,%d)" % (x, y, w, h))
            self.image = self.image.crop((x, y, x + w, y + h))
            self.width = w
            self.height = h

    def do_size(self, w, h):
        """Apply size scaling."""
        if (w is None):
            self.logger.debug("size: no scaling (nop)")
        else:
            self.logger.debug("size: scaling to (%d,%d)" % (w, h))
            self.image = self.image.resize((w, h))
            self.width = w
            self.height = h

    def do_rotation(self, mirror, rot):
        """Apply rotation and/or mirroring."""
        if (not mirror and rot == 0.0):
            self.logger.debug("rotation: no rotation (nop)")
        else:
            # FIXME - with PIL one can use the transpose() method to do 90deg
            # FIXME - rotations as well as mirroring. This would be more efficient
            # FIXME - for these cases than mirror _then_ rotate.
            if (mirror):
                self.logger.debug("rotation: mirror (about vertical axis)")
                self.image = self.image.transpose(Image.FLIP_LEFT_RIGHT)
            if (rot != 0.0):
                self.logger.debug("rotation: by %f degrees clockwise" % (rot))
                self.image = self.image.rotate(-rot, expand=True)

    def do_quality(self, quality):
        """Apply value of quality parameter.

        For PIL docs see
        <http://pillow.readthedocs.org/en/latest/reference/Image.html#PIL.Image.Image.convert>
        """
        if (quality == 'grey' or quality == 'gray'):
            # Checking for 1.1 gray or 20.0 grey elsewhere
            self.logger.debug("quality: converting to gray")
            self.image = self.image.convert('L')
        elif (quality == 'bitonal'):
            self.logger.debug("quality: converting to bitonal")
            self.image = self.image.convert('1')
        elif (self.image.mode not in ('1', 'L', 'RGB', 'RGBA')):
            # Need to convert from palette etc. in order to write out
            self.logger.debug("quality: converting from mode %s to RGB"
                              % (self.image.mode))
            self.image = self.image.convert('RGB')
        else:
            self.logger.debug("quality: quality (nop)")

    def do_format(self, format):
        """Apply format selection.

        Assume that for tiling applications we want jpg so return
        that unless an explicit format is requested.
        """
        fmt = ('jpg' if (format is None) else format)
        if (fmt == 'png'):
            self.logger.debug("format: png")
            self.mime_type = "image/png"
            self.output_format = fmt
            format = 'png'
        elif (fmt == 'jpg'):
            self.logger.debug("format: jpg")
            self.mime_type = "image/jpeg"
            self.output_format = fmt
            format = 'jpeg'
        elif (fmt == 'webp'):
            self.logger.debug("format: webp")
            self.mime_type = "image/webp"
            self.output_format = fmt
            format = 'webp'
        else:
            raise IIIFError(code=415, parameter='format',
                            text="Unsupported output file format (%s), only png,jpg,webp are supported." % (fmt))
        if (self.outfile is None):
            # Create temp
            f = tempfile.NamedTemporaryFile(delete=False)
            self.outfile = f.name
            self.outtmp = f.name
            self.image.save(f, format=format)
        else:
            # Save to specified location
            self.image.save(self.outfile, format=format)

    def cleanup(self):
        """Cleanup temporary output file."""
        if (self.outtmp is not None):
            try:
                os.unlink(self.outtmp)
            except OSError as e:
                self.logger.warning("Failed to cleanup tmp output file %s"
                                    % (self.outtmp))
