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

from .manipulator_pil import IIIFManipulatorPIL
from .manipulator_gen import IIIFManipulatorGen
from .info import IIIFInfo
from .request import IIIFRequest
from .error import IIIFZeroSizeError


def static_partial_tile_sizes(width, height, tilesize, scale_factors):
    """Generator for partial tile sizes for zoomed in views.

    Positional arguments:
    width -- width of full size image
    height -- height of full size image
    tilesize -- width and height of tiles
    scale_factors -- iterable of scale factors, typically [1,2,4..]

    Yields ([rx,ry,rw,rh],[sw,sh]), the region and size for each tile
    """
    for sf in scale_factors:
        if (sf * tilesize >= width and sf * tilesize >= height):
            continue  # avoid any full-region tiles
        rts = tilesize * sf  # tile size in original region
        xt = (width - 1) // rts + 1
        yt = (height - 1) // rts + 1
        for nx in range(xt):
            rx = nx * rts
            rxe = rx + rts
            if (rxe > width):
                rxe = width
            rw = rxe - rx
            # same as sw = int(math.ceil(rw/float(sf)))
            sw = (rw + sf - 1) // sf
            for ny in range(yt):
                ry = ny * rts
                rye = ry + rts
                if (rye > height):
                    rye = height
                rh = rye - ry
                # same as sh = int(math.ceil(rh/float(sf)))
                sh = (rh + sf - 1) // sf
                yield([rx, ry, rw, rh], [sw, sh])


def static_full_sizes(width, height, tilesize):
    """Generator for scaled-down full image sizes.

    Positional arguments:
    width -- width of full size image
    height -- height of full size image
    tilesize -- width and height of tiles

    Yields [sw,sh], the size for each full-region tile that is less than
    the tilesize. This includes tiles up to the full image size if that
    is smaller than the tilesize.
    """
    # FIXME - Not sure what correct algorithm is for this, from
    # observation of Openseadragon it seems that one keeps halving
    # the pixel size of the full image until until both width and
    # height are less than the tile size. After that all subsequent
    # halving of the image size are used, all the way down to 1,1.
    # It seems that without these reduced size full-region images,
    # OpenSeadragon will not display any unzoomed image in small windows.
    #
    # I do not understand the algorithm that OpenSeadragon uses (or
    # know where it is in the code) to decide how small a version of
    # the complete image to request. It seems that there is a bug in
    # OpenSeadragon here because in some cases it requests images
    # of size 1,1 multiple times, which is anyway a useless image.
    for level in range(0, 20):
        factor = 2.0**level
        sw = int(width / factor + 0.5)
        sh = int(height / factor + 0.5)
        if (sw < tilesize and sh < tilesize):
            if (sw < 1 or sh < 1):
                break
            yield([sw, sh])


class IIIFStaticError(Exception):
    """Error class for errors to be resported to user."""

    pass


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

    The class is quite noisy at level logging.INFO, set the logging
    level to logging.WARNING to get log output only when there are
    warnings or errors.
    """

    def __init__(self, src=None, dst=None, tilesize=None,
                 api_version='2.0', dryrun=None, prefix='',
                 osd_version=None, generator=False,
                 max_image_pixels=0, extras=[]):
        """Initialization for IIIFStatic instances.

        All keyword arguments are optional:
        src -- source image file
        dst -- destination directory
        tilesize -- size of square tiles to generate (default 512)
        api_version -- IIIF Image API version to support (default 2.0)
        dryrun -- True to not write any output (default None)
        prefix -- identifier prefix
        osd_version -- use a specific version of OpenSeadragon
        extras -- extras request parameters to generate for
        """
        self.src = src
        self.dst = dst
        self.tilesize = tilesize if tilesize is not None else 512
        self.api_version = api_version
        if (self.api_version == '1'):
            self.api_version = '1.1'
        elif (self.api_version == '2'):
            self.api_version = '2.0'
        self.dryrun = (dryrun is not None)
        self.logger = logging.getLogger(__name__)
        self.prefix = prefix
        self.osd_version = osd_version if osd_version else '2.0.0'
        if (generator):
            self.manipulator_klass = IIIFManipulatorGen
        else:
            self.manipulator_klass = IIIFManipulatorPIL
        self.max_image_pixels = max_image_pixels
        # parse values in extras before adding to list, remove any leading /
        # if present on extras values
        self.extras = []
        for extra in extras:
            self.extras.append(self.parse_extra(extra))
        # config for locations of OpenSeadragon
        # - dir is relative to base, will be copied to dir under html_dir
        # - js and images are relative to dir
        self.module_dir = os.path.dirname(__file__)
        self.osd_config = {
            '1.0.0': {
                'base': os.path.join(self.module_dir, 'third_party'),
                'dir': 'openseadragon100',
                'js': 'openseadragon.min.js',
                'images': 'images',
                'use_canonical': False,
                'notes': 'Uses /w,h/ for size, algorithm not quite right, API v1.1'
            },
            '1.2.1': {
                'base': os.path.join(self.module_dir, 'third_party'),
                'dir': 'openseadragon121',
                'js': 'openseadragon.min.js',
                'images': 'images',
                'use_canonical': True,
                'notes': "Uses /w,/ canonical syntax, works with API v1.1,2.0"
            },
            '2.0.0': {
                'base': os.path.join(self.module_dir, 'third_party'),
                'dir': 'openseadragon200',
                'js': 'openseadragon.min.js',
                'images': 'images',
                'use_canonical': True,
                'notes': "Uses /w,/ canonical syntax, works with API v1.1,2.0"
            }
        }
        # used internally:
        self.identifier = None
        self.copied_osd = False
        self.template_dir = os.path.join(self.module_dir, 'templates')

    def parse_extra(self, extra):
        """Parse extra request parameters to IIIFRequest object."""
        if extra.startswith('/'):
            extra = extra[1:]
        r = IIIFRequest(identifier='dummy',
                        api_version=self.api_version)
        r.parse_url(extra)
        if (r.info):
            raise IIIFStaticError("Attempt to specify Image Information in extras.")
        return(r)

    def get_osd_config(self, osd_version):
        """Select appropriate portion of config.

        If the version requested is not supported the raise an exception with
        a helpful error message listing the versions supported.
        """
        if (osd_version in self.osd_config):
            return(self.osd_config[osd_version])
        else:
            raise IIIFStaticError("OpenSeadragon version %s not supported, available versions are %s" %
                                  (osd_version, ', '.join(sorted(self.osd_config.keys()))))

    def generate(self, src=None, identifier=None):
        """Generate static files for one source image."""
        self.src = src
        self.identifier = identifier
        # Get image details and calculate tiles
        im = self.manipulator_klass()
        im.srcfile = self.src
        im.set_max_image_pixels(self.max_image_pixels)
        im.do_first()
        width = im.width
        height = im.height
        scale_factors = im.scale_factors(self.tilesize)
        # Setup destination and IIIF identifier
        self.setup_destination()
        # Write out images
        for (region, size) in static_partial_tile_sizes(width, height, self.tilesize, scale_factors):
            self.generate_tile(region, size)
        sizes = []
        for size in static_full_sizes(width, height, self.tilesize):
            # See https://github.com/zimeon/iiif/issues/9
            sizes.append({'width': size[0], 'height': size[1]})
            self.generate_tile('full', size)
        for request in self.extras:
            request.identifier = self.identifier
            if (request.is_scaled_full_image()):
                sizes.append({'width': request.size_wh[0],
                              'height': request.size_wh[1]})
            self.generate_file(request)
        # Write info.json
        qualities = ['default'] if (self.api_version > '1.1') else ['native']
        info = IIIFInfo(level=0, server_and_prefix=self.prefix, identifier=self.identifier,
                        width=width, height=height, scale_factors=scale_factors,
                        tile_width=self.tilesize, tile_height=self.tilesize,
                        formats=['jpg'], qualities=qualities, sizes=sizes,
                        api_version=self.api_version)
        json_file = os.path.join(self.dst, self.identifier, 'info.json')
        if (self.dryrun):
            self.logger.warning(
                "dryrun mode, would write the following files:")
            self.logger.warning("%s / %s/%s" %
                                (self.dst, self.identifier, 'info.json'))
        else:
            with open(json_file, 'w') as f:
                f.write(info.as_json())
                f.close()
            self.logger.info("%s / %s/%s" %
                             (self.dst, self.identifier, 'info.json'))
            self.logger.debug("Written %s" % (json_file))

    def generate_tile(self, region, size):
        """Generate one tile for this given region, size of this image."""
        r = IIIFRequest(identifier=self.identifier,
                        api_version=self.api_version)
        if (region == 'full'):
            r.region_full = True
        else:
            r.region_xywh = region  # [rx,ry,rw,rh]
        r.size_wh = size  # [sw,sh]
        r.format = 'jpg'
        self.generate_file(r, True)

    def generate_file(self, r, undistorted=False):
        """Generate file for IIIFRequest object r from this image.

        FIXME - Would be nicer to have the test for an undistorted image request
        based on the IIIFRequest object, and then know whether to apply canonicalization
        or not.

        Logically we might use `w,h` instead of the Image API v2.0 canonical
        form `w,` if the api_version is 1.x. However, OSD 1.2.1 and 2.x assume
        the new canonical form even in the case where the API version is declared
        earlier. Thus, determine whether to use the canonical or `w,h` form based
        solely on the setting of osd_version.
        """
        use_canonical = self.get_osd_config(self.osd_version)['use_canonical']
        height = None
        if (undistorted and use_canonical):
            height = r.size_wh[1]
            r.size_wh = [r.size_wh[0], None]  # [sw,sh] -> [sw,]
        path = r.url()
        # Generate...
        if (self.dryrun):
            self.logger.info("%s / %s" % (self.dst, path))
        else:
            m = self.manipulator_klass(api_version=self.api_version)
            try:
                m.derive(srcfile=self.src, request=r,
                         outfile=os.path.join(self.dst, path))
                self.logger.info("%s / %s" % (self.dst, path))
            except IIIFZeroSizeError:
                self.logger.info("%s / %s - zero size, skipped" %
                                 (self.dst, path))
                return  # done if zero size
        if (r.region_full and use_canonical and height is not None):
            # In v2.0 of the spec, the canonical URI form `w,` for scaled
            # images of the full region was introduced. This is somewhat at
            # odds with the requirement for `w,h` specified in `sizes` to
            # be available, and has problems of precision with tall narrow
            # images. Hopefully will be fixed in 3.0 but for now symlink
            # the `w,h` form to the `w,` dirs so that might use the specified
            # `w,h` also work. See
            # <https://github.com/IIIF/iiif.io/issues/544>
            #
            # FIXME - This is ugly because we duplicate code in
            # iiif.request.url to construct the partial URL
            region_dir = os.path.join(r.quote(r.identifier), "full")
            wh_dir = "%d,%d" % (r.size_wh[0], height)
            wh_path = os.path.join(region_dir, wh_dir)
            wc_dir = "%d," % (r.size_wh[0])
            wc_path = os.path.join(region_dir, wc_dir)
            if (not self.dryrun):
                ln = os.path.join(self.dst, wh_path)
                if (os.path.exists(ln)):
                    os.remove(ln)
                os.symlink(wc_dir, ln)
            self.logger.info("%s / %s -> %s" % (self.dst, wh_path, wc_path))

    def setup_destination(self):
        """Setup output directory based on self.dst and self.identifier.

        Returns the output directory name on success, raises and exception on
        failure.
        """
        # Do we have a separate identifier?
        if (not self.identifier):
            # No separate identifier specified, split off the last path segment
            # of the source name, strip the extension to get the identifier
            self.identifier = os.path.splitext(os.path.split(self.src)[1])[0]
        # Done if dryrun, else setup self.dst first
        if (self.dryrun):
            return
        if (not self.dst):
            raise IIIFStaticError("No destination directory specified!")
        dst = self.dst
        if (os.path.isdir(dst)):
            # Exists, OK
            pass
        elif (os.path.isfile(dst)):
            raise IIIFStaticError(
                "Can't write to directory %s: a file of that name exists" % dst)
        else:
            os.makedirs(dst)
        # Second, create identifier based subdir if necessary
        outd = os.path.join(dst, self.identifier)
        if (os.path.isdir(outd)):
            # Nothing for now, perhaps should delete?
            self.logger.warning(
                "Output directory %s already exists, adding/updating files" % outd)
            pass
        elif (os.path.isfile(outd)):
            raise IIIFStaticError(
                "Can't write to directory %s: a file of that name exists" % outd)
        else:
            os.makedirs(outd)
        self.logger.debug("Output directory %s" % outd)

    def write_html(self, html_dir='/tmp', include_osd=False,
                   osd_width=500, osd_height=500):
        """Write HTML test page using OpenSeadragon for the tiles generated.

        Assumes that the generate(..) method has already been called to set up
        identifier etc. Parameters:
          html_dir - output directory for HTML files, will be created if it
                     does not already exist
          include_osd - true to include OpenSeadragon code
          osd_width - width of OpenSeadragon pane in pixels
          osd_height - height of OpenSeadragon pane in pixels
        """
        osd_config = self.get_osd_config(self.osd_version)
        osd_base = osd_config['base']
        osd_dir = osd_config['dir']  # relative to base
        osd_js = os.path.join(osd_dir, osd_config['js'])
        osd_images = os.path.join(osd_dir, osd_config['images'])
        if (os.path.isdir(html_dir)):
            # Exists, fine
            pass
        elif (os.path.isfile(html_dir)):
            raise IIIFStaticError(
                "Can't write to directory %s: a file of that name exists" % html_dir)
        else:
            os.makedirs(html_dir)
        self.logger.info("Writing HTML to %s" % (html_dir))
        with open(os.path.join(self.template_dir, 'static_osd.html'), 'r') as f:
            template = f.read()
        outfile = self.identifier + '.html'
        outpath = os.path.join(html_dir, outfile)
        with open(outpath, 'w') as f:
            info_json_uri = '/'.join([self.identifier, 'info.json'])
            if (self.prefix):
                info_json_uri = '/'.join([self.prefix, info_json_uri])
            d = dict(identifier=self.identifier,
                     api_version=self.api_version,
                     osd_version=self.osd_version,
                     osd_uri=osd_js,
                     osd_images_prefix=osd_images,
                     osd_height=osd_width,
                     osd_width=osd_height,
                     info_json_uri=info_json_uri)
            f.write(Template(template).safe_substitute(d))
            self.logger.info("%s / %s" % (html_dir, outfile))
        # Do we want to copy OSD in there too? If so, do it only if
        # we haven't already
        if (include_osd):
            if (self.copied_osd):
                self.logger.info("OpenSeadragon already copied")
            else:
                # Make directory, copy JavaScript and icons (from osd_images)
                osd_path = os.path.join(html_dir, osd_dir)
                if (not os.path.isdir(osd_path)):
                    os.makedirs(osd_path)
                shutil.copyfile(os.path.join(osd_base, osd_js),
                                os.path.join(html_dir, osd_js))
                self.logger.info("%s / %s" % (html_dir, osd_js))
                osd_images_path = os.path.join(html_dir, osd_images)
                if (os.path.isdir(osd_images_path)):
                    self.logger.warning(
                        "OpenSeadragon images directory (%s) already exists, skipping"
                        % osd_images_path)
                else:
                    shutil.copytree(os.path.join(osd_base, osd_images),
                                    osd_images_path)
                    self.logger.info("%s / %s/*" % (html_dir, osd_images))
                self.copied_osd = True  # don't try again for next img
