"""Static file generation for IIIF Image API.

Use IIIF Image API manipulations to generate a set of tiles for
a level0 implementation of the IIIF Image API using static files.
"""

import math
import logging
import os
import os.path
import shutil
from string import Template

from iiif.manipulator_pil import IIIFManipulatorPIL
from iiif.info import IIIFInfo
from iiif.request import IIIFRequest
from iiif.error import IIIFZeroSizeError


def static_partial_tile_sizes(width,height,tilesize,scale_factors):
    """Generator for partial tile sizes for zoomed in views.

    Positional arguments:
    width -- width of full size image
    height -- height of full size image
    tilesize -- width and height of tiles
    scale_factors -- iterable of scale factors, typically [1,2,4..]

    Yields ([rx,ry,rw,rh],[sw,sh]), the region and size for each tile
    """
    for sf in scale_factors:
        if (sf*tilesize>=width and sf*tilesize>=height):
            continue #avoid any full-region tiles
        rts = tilesize*sf #tile size in original region
        xt = (width-1)/rts+1
        yt = (height-1)/rts+1
        for nx in range(xt):
            rx = nx*rts
            rxe = rx+rts
            if (rxe>width):
                rxe=width
            rw = rxe-rx
            sw = (rw+sf-1)/sf #same as sw = int(math.ceil(rw/float(sf)))
            for ny in range(yt):
                ry = ny*rts
                rye = ry+rts
                if (rye>height):
                    rye=height
                rh = rye-ry
                sh = (rh+sf-1)/sf #same as sh = int(math.ceil(rh/float(sf)))
                yield([rx,ry,rw,rh],[sw,sh])


def static_full_sizes(width,height,tilesize):
    """Generator for scaled-down full image sizes.

    Positional arguments:
    width -- width of full size image
    height -- height of full size image
    tilesize -- width and height of tiles

    Yields [sw,sh], the size for each full-region tile 
    """
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
        if (sw<tilesize and sh<tilesize):
            if (sw<1 or sh<1):
                break
            yield([sw,sh])


class IIIFStatic(object):

    """Provide static generation of IIIF images.

    Simplest, using source image as model for directory which
    will be in same directory without extension:

        IIIFStatic("image1.jpg").generate()

    More complex with different output directory but using name
    derived from image:

        sg = IIIFStatic(dst="outdir")
        sg.generate("image2.jpg")
        sg.generate("image3.jpg")

    """

    def __init__(self, src=None, dst=None, tilesize=None,
                 api_version='2.0', dryrun=None, prefix=''):
        """Initialization for IIIFStatic instances.

        All keyword arguments are optional:
        src -- source image file
        dst -- destination directory
        tilesize -- size of square tiles to generate (default 512)
        api_version -- IIIF Image API version to support (default 2.0)
        dryrun -- True to not write any output (default None)
        prefix -- identifier prefix
        """
        self.src = src
        self.dst = dst
        self.tilesize = tilesize if tilesize is not None else 512
        self.api_version = api_version
        if (self.api_version=='1'):
            self.api_version = '1.1'
        elif (self.api_version=='2'):
            self.api_version = '2.0'
        self.dryrun = (dryrun is not None)
        self.logger = logging.getLogger(__name__)
        # used internally:
        self.prefix = prefix
        self.identifier = None
        self.copied_osd = False
        self.template_dir = os.path.join(os.path.dirname(__file__), 'templates')


    def generate(self, src=None, identifier=None):
        """Generate static files for one source image."""
        self.src=src
        self.identifier=identifier
        # Get image details and calculate tiles
        im=IIIFManipulatorPIL()
        im.srcfile = self.src
        im.do_first()
        width = im.width
        height = im.height
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
        # Write out images
        for (region,size) in static_partial_tile_sizes(width,height,self.tilesize,scale_factors):
            self.generate_tile(region,size)
        sizes = []
        for (size) in static_full_sizes(width,height,self.tilesize):
            #FIXME - see https://github.com/zimeon/iiif/issues/9
            #sizes.append({'width': size[0], 'height': size[1]})
            self.generate_tile('full',size)
        # Write info.json
        qualities = ['default'] if (self.api_version>'1.1') else ['native']
        info=IIIFInfo(level=0, server_and_prefix=self.prefix, identifier=self.identifier,
                      width=width, height=height, scale_factors=scale_factors,
                      tile_width=self.tilesize, tile_height=self.tilesize,
                      formats=['jpg'], qualities=qualities, sizes=sizes,
                      api_version=self.api_version)
        json_file = os.path.join(self.dst,self.identifier,'info.json')
        if (self.dryrun):
            print "dryrun mode, would write the following files:"
            print "%s / %s/%s" % (self.dst, self.identifier, 'info.json')
            self.logger.info(info.as_json())
        else:
            with open(json_file,'w') as f:
                f.write(info.as_json())
                f.close()
            self.logger.info("Written %s"%(json_file))
        print


    def generate_tile(self,region,size):
        """Generate one tile for this given region,size of this region."""
        r = IIIFRequest(identifier=self.identifier,api_version=self.api_version)
        if (region == 'full'):
            r.region_full = True
        else:
            r.region_xywh = region # [rx,ry,rw,rh]
        r.size_wh = [size[0],None] # [sw,sh] -> [sw,] canonical form
        r.format = 'jpg'
        path = r.url()
        # Generate...
        if (self.dryrun):
            print "%s / %s" % (self.dst,path)
        else:
            m = IIIFManipulatorPIL(api_version=self.api_version)
            try:
                m.derive(srcfile=self.src, request=r, outfile=os.path.join(self.dst,path))
                print "%s / %s" % (self.dst,path)
            except IIIFZeroSizeError as e:
                print "%s / %s - zero size, skipped" % (self.dst,path)


    def setup_destination(self):
        """Setup output directory based on self.dst and self.identifier.

        Returns the output directory name on success, raises and exception on
        failure.
        """
        if (not self.dst):
            raise Exception("No destination directory specified!")
        dst = self.dst
        if (os.path.isdir(dst)):
            # Exists, OK
            pass
        elif (os.path.isfile(dst)):
            raise Exception("Can't write to directory %s: a file of that name exists" % dst)
        else:
            os.makedirs(dst)
        # Now have dst directory, do we have a separate identifier?
        if (not self.identifier):
            # No separate identifier specified, split off the last path segment
            # of the source name, strip the extension to get the identifier
            self.identifier = os.path.splitext( os.path.split(self.src)[1] )[0]
        # Create that subdir if necessary
        outd = os.path.join(dst,self.identifier)
        if (os.path.isdir(outd)):
            # Nothing for now, perhaps should delete?
            self.logger.warn("Output directory %s already exists, adding/updating files" % outd)
            pass
        elif (os.path.isfile(outd)):
            raise Exception("Can't write to directory %s: a file of that name exists" % outd)
        else:
            os.makedirs(outd)
        #
        self.logger.info("Output directory %s" % outd)


    def write_html(self, html_dir, include_osd=False):
        """Write HTML test page using OpenSeadragon for the tiles generated.

        Assumes that the generate(..) method has already been called to set up
        identifier etc.
        """
        osd_dir = 'osd'
        osd_js = 'osd/openseadragon.min.js'
        osd_images = 'osd/images'
      
        if (os.path.isdir(html_dir)):
            # Exists, fine
            pass
        elif (os.path.isfile(html_dir)):
            raise Exception("Can't write to directory %s: a file of that name exists" % html_dir)
        else:
            os.makedirs(html_dir)
        with open(os.path.join(self.template_dir,'static_osd.html'),'r') as f:
            template = f.read()
        outfile = self.identifier+'.html'
        outpath = os.path.join(html_dir,outfile)
        with open(outpath,'w') as f:
            info_json_uri = '/'.join([self.identifier,'info.json'])
            if (self.prefix):
                info_json_uri = '/'.join([self.prefix,info_json_uri])
            d = dict( identifier = self.identifier,
                      osd_uri = osd_js,
                      osd_images_prefix = osd_images+'/', #OSD needs trailing slash
                      info_json_uri = info_json_uri )
            f.write( Template(template).safe_substitute(d) )
            print "%s / %s" % (html_dir,outfile)
            self.logger.info("Wrote info.json to %s" % outpath)
        # Do we want to copy OSD in there too? If so, do it only if
        # we haven't already
        if (include_osd):
            if (self.copied_osd):
                self.logger.info("OpenSeadragon already copied")
            else:
                # Make directory, copy JavaScript and icons (from osd_images)
                osd_path = os.path.join(html_dir,osd_dir)
                if (not os.path.isdir(osd_path)):
                    os.makedirs(osd_path)
                shutil.copyfile(os.path.join('demo-static',osd_js), os.path.join(html_dir,osd_js))
                print "%s / %s" % (html_dir,osd_js)
                osd_images_path = os.path.join(html_dir,osd_images)
                if (os.path.isdir(osd_images_path)):
                    self.logger.warn("OpenSeadragon images directory (%s) already exists, skipping" % osd_images_path)
                else:
                    shutil.copytree(os.path.join('demo-static',osd_images), osd_images_path)
                    print "%s / %s/*" % (html_dir,osd_images)
        print



