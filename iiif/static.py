"""Static file generation for IIIF Image API

Use IIIF Image API manipulations to generate a set of tiles for
a level0 implementation of the IIIF Image API using static files.
"""

from iiif import __api_major__,__api_minor__
from iiif.manipulator_pil import IIIFManipulatorPIL
from iiif.info import IIIFInfo
from iiif.request import IIIFRequest

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

    def __init__(self, src=None, dst=None, tilesize=None):
        self.src=src
        self.dst=dst
        self.identifier='./img'
        self.tilesize=tilesize if tilesize is not None else 512

    def generate(self, src=None, dst=None, tilesize=None):
        # Use attributes as defaults for params not specified
        if (src is None):
            src=self.src
        if (dst is None):
            dst=self.dst
        if (tilesize is None):
            tilesize=self.tilesize
        # Get image details and calculate tiles
        im=IIIFManipulatorPIL()
        im.srcfile=src
        im.do_first()
        width=im.width
        height=im.height
        #print "w=%d h=%d ts=%d" % (im.width,im.height,tilesize)
        xtiles = int(width/tilesize)
        ytiles = int(height/tilesize)
        max_tiles = xtiles if (xtiles>ytiles) else ytiles
        scale_factors = [ 1 ]
        factor = 1
        for n in range(10):
            if (factor >= max_tiles):
                break
            factor = factor+factor
            scale_factors.append(factor)
        # Write info.json
        info=IIIFInfo(level=0, identifier=self.identifier,
                      width=width, height=height, scale_factors=scale_factors,
                      tile_width=tilesize, tile_height=tilesize,
                      formats=['jpg'], qualities=['native'])
        print info.as_json()
        # Write out images
        for sf in scale_factors:
            rts = tilesize*sf #tile size in original region
            xt = (width-1)/rts+1 
            yt = (height-1)/rts+1
            for nx in range(xt):
                rx = nx*rts
                rxe = rx+rts
                if (rxe>width):
                    rxe=width-1
                rw = rxe-rx
                sw = rw/sf
                for ny in range(yt):
                    ry = ny*rts
                    rye = ry+rts
                    if (rye>height):
                        rye=height-1
                    rh = rye-ry
                    sh = rh/sf
                    self.generate_tile(rx,ry,rw,rh,sw,sh)

    def generate_tile(self,rx,ry,rw,rh,sw,sh):
        r = IIIFRequest(identifier="aa")
        r.region_xywh=[rx,ry,rw,rh]
        r.size_wh=[sw,sh]
        path = r.url()
        print path
        #m = IIIFManipulator()
        #m.derive(srcfile='a.jpg',request=r)        
