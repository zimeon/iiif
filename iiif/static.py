"""Static file generation for IIIF Image API

Use IIIF Image API manipulations to generate a set of tiles for
a level0 implementation of the IIIF Image API using static files.
"""

from iiif import __api_major__,__api_minor__

class IIIFStatic:
    """Provide static generation of IIIF images

    Simplest, using source image as model for directory which
    will be in same directory without extension: 

        IIIFStatic("image1.jpg").generate()

    More complex with different output directory but using name
    derived from image:
    
        sg = IIIFStatic(dst="outdir")
        sg.generate("image2.jpg")
        sg.generate("image3.jpg")
    """

    def __init__(self, src=None, dst=None, tilesize=512):
        pass

    def generate(self, src=None, dst=None, tilesize=None):
        # Use attributes as defaults for params not specified
        if (src is None):
            src=self.src
        if (dst is None):
            dst=self.dst
        if (tilesize is None):
            tilesize=self.tilesize



       

