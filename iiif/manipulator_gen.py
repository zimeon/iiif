"""Generator for IIIF Image API using the Python Image Library."""

import os.path
import sys

from PIL import Image

from .error import IIIFError
from .manipulator_pil import IIIFManipulatorPIL


class IIIFManipulatorGen(IIIFManipulatorPIL):
    """Class to generate an image with PIL according to IIIF Image API.

    Implemented as a small set of modifications to patch the generaton
    into the IIIFManipulatorPIL class which already handles rotation,
    quality and format parameters, and saving the image file.

    All exceptions are raised as IIIFError objects which directly
    determine the HTTP response.
    """

    def __init__(self, **kwargs):
        """Initialize IIIFManipulatorGen object.

        Keyword arguments are passed to superclass initialize method
        """
        super(IIIFManipulatorGen, self).__init__(**kwargs)
        self.gen = None

    def do_first(self):
        """Load generator, set size.

        We take the generator module name from self.srcfile so that
        this manipulator will work with different generators in a
        similar way to how the ordinary generators work with
        different images
        """
        # Load generator module and create instance if we haven't already
        if (not self.srcfile):
            raise IIIFError(text=("No generator specified"))
        if (not self.gen):
            try:
                (name, ext) = os.path.splitext(self.srcfile)
                (pack, mod) = os.path.split(name)
                module_name = 'iiif.generators.' + mod
                try:
                    module = sys.modules[module_name]
                except KeyError:
                    self.logger.debug(
                        "Loading generator module %s" % (module_name))
                    # Would be nice to use importlib but this is available only
                    # in python 2.7 and higher
                    pack = __import__(module_name)  # returns iiif package
                    module = getattr(pack.generators, mod)
                self.gen = module.PixelGen()
            except ImportError:
                raise IIIFError(
                    text=("Failed to load generator %s" % (str(self.srcfile))))
        (self.width, self.height) = self.gen.size

    def do_region(self, x, y, w, h):
        """Record region."""
        if (x is None):
            self.rx = 0
            self.ry = 0
            self.rw = self.width
            self.rh = self.height
        else:
            self.rx = x
            self.ry = y
            self.rw = w
            self.rh = h

    def do_size(self, w, h):
        """Record size."""
        if (w is None):
            self.sw = self.rw
            self.sh = self.rh
        else:
            self.sw = w
            self.sh = h
        # Now we have region and size, generate the image
        image = Image.new("RGB", (self.sw, self.sh), self.gen.background_color)
        for y in range(0, self.sh):
            for x in range(0, self.sw):
                ix = int((x * self.rw) // self.sw + self.rx)
                iy = int((y * self.rh) // self.sh + self.ry)
                color = self.gen.pixel(ix, iy)
                if (color is not None):
                    image.putpixel((x, y), color)
        self.image = image
