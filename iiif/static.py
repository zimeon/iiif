"""Static file generation for IIIF Image API

Use IIIF Image API manipulations to generate a set of tiles for
a level0 implementation of the IIIF Image API using static files.
"""

import logging
import os
import os.path

from iiif.manipulator_pil import IIIFManipulatorPIL
from iiif.info import IIIFInfo
from iiif.request import IIIFRequest

class IIIFStatic(object):
    """Provide static generation of IIIF images

    Simplest, using source image as model for directory which
    will be in same directory without extension: 

        IIIFStatic("image1.jpg").generate()

    More complex with different output directory but using name
    derived from image:
    
        sg = IIIFStatic(dst="outdir")
        sg.generate("image2.jpg")
        sg.generate("image3.jpg")

    If prefix is set then this is appended as another path element on dst
    to specify the output directory.
    """

    def __init__(self, src=None, dst=None, prefix=None, tilesize=None, 
                 api_version=None, dryrun=None):
        self.src=src
        self.dst=dst
        self.prefix=prefix
        self.tilesize=tilesize if tilesize is not None else 512
        self.api_version=api_version if api_version is not None else '1.1'
        if (self.api_version=='1'):
            self.api_version='1.1'
        elif (self.api_version=='2'):
            self.api_version='2.0'
        self.dryrun = (dryrun is not None)
        self.logger = logging.getLogger('iiif_static')
        # used internally:
        self.outd=None
        self.identifier=None

    def generate(self, src=None, dst=None, tilesize=None):
        # Use params to override object attributes
        if (src is not None):
            self.src=src
        if (dst is not None):
            self.dst=dst
        if (tilesize is not None):
            self.tilesize=tilesize
        # Get image details and calculate tiles
        im=IIIFManipulatorPIL()
        im.srcfile=self.src
        im.do_first()
        width=im.width
        height=im.height
        #print "w=%d h=%d ts=%d" % (im.width,im.height,tilesize)
        xtiles = int(width/self.tilesize)
        ytiles = int(height/self.tilesize)
        max_tiles = xtiles if (xtiles>ytiles) else ytiles
        scale_factors = [ 1 ]
        factor = 1
        for n in range(10):
            if (factor >= max_tiles):
                break
            factor = factor+factor
            scale_factors.append(factor)
        # Setup destination and IIIF identifier
        self.setup_destination()
        if (self.identifier is None):
            (self.identifier,ext) = os.path.splitext(os.path.basename(self.dst))
        # Write info.json
        qualities = ['default'] if (self.api_version>'1.1') else ['native']
        info=IIIFInfo(level=0, identifier=self.identifier,
                      width=width, height=height, scale_factors=scale_factors,
                      tile_width=self.tilesize, tile_height=self.tilesize,
                      formats=['jpg'], qualities=qualities,
                      api_version=self.api_version)
        json_file=os.path.join(self.dst,self.identifier,'info.json')
        if (self.dryrun):
            print "dryrun mode, would write the following files:"
            print "%s / %s" % (self.dst, os.path.join(self.identifier,'info.json'))
            self.logger.info(info.as_json())
        else:
            with open(json_file,'w') as f:
                f.write(info.as_json())
                f.close()
            self.logger.info("Written %s"%(json_file))
        # Write out images
        for sf in scale_factors:
            rts = self.tilesize*sf #tile size in original region
            xt = (width-1)/rts+1 
            yt = (height-1)/rts+1
            for nx in range(xt):
                rx = nx*rts
                rxe = rx+rts
                if (rxe>width):
                    rxe=width
                rw = rxe-rx
                sw = rw/sf
                for ny in range(yt):
                    ry = ny*rts
                    rye = ry+rts
                    if (rye>height):
                        rye=height
                    rh = rye-ry
                    sh = rh/sf
                    self.generate_tile([rx,ry,rw,rh],[sw,sh])
        # Now generate reduced size versions of full image
        # 
        # FIXME - Not sure what correct algorithm is for this, from
        # observation of Openseadragon it seems that one keeps halving
        # the pixel size of the full until until both width and height
        # are less than the tile size. The output that tile and further
        # halvings for some time. It seems that without this Openseadragon
        # will not display any unzoomed image in small windows.
        #
        # I do not understand the algorithm that openseadragon uses (or
        # know where it is in the code) to decide how small a version of
        # the complete image to request. It seems that there is a bug in
        # openseadragon here because in some cases it requests images
        # of size 1,1 multiple times. For now, just go all the way down to 
        # this size
        for level in range(1,20):
            factor = 2.0**level
            sw = int(width/factor + 0.5)
            sh = int(height/factor + 0.5)
            if (sw<self.tilesize and sh<self.tilesize):
                if (sw<1 or sh<1):
                    break
                self.generate_tile('full',[sw,sh])

    def generate_tile(self,region,size):
        r = IIIFRequest(identifier=self.identifier,api_version=self.api_version)
        if (region == 'full'):
            r.region_full = True
        else:
            r.region_xywh=region # [rx,ry,rw,rh]
        r.size_wh=size # [sw,sh]
        r.format='jpg'
        path = r.url()
        print "%s / %s" % (self.dst,path)
        # Generate...
        if (not self.dryrun):
            m = IIIFManipulatorPIL(api_version=self.api_version)
            m.derive(srcfile=self.src, request=r, outfile=os.path.join(self.dst,path))        

    def setup_destination(self):
        """Setup output directory based on self.dst and self.prefix

        Returns the output directory name on success, raises and exception on
        failure. 
        """
        outd = self.dst
        if (self.dst is None):
            # derive output dir from src
            (outd, junk) = os.path.splitext(self.src)
        if (self.prefix):
            outd = os.path.join(outd,self.prefix)
        if (os.path.isdir(outd)):
            # Nothing for now, perhaps should delete?
            pass
        elif (os.path.isfile(self.outd)):
            raise Exception("Can't write to directory %s: a file of that name exists"%(self.outd))
        else:
            os.makedirs(outd)
        # Now chop off 'identifier' directory
        (self.outd, self.identifier) = os.path.split(self.dst)
        self.logger.info("Output directory %s" % (self.outd))
