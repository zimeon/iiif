#!/usr/bin/env python
"""iiif_static: Generate static images implementing the IIIF Image API level 0.

Copyright 2014--2018 Simeon Warner
"""

import logging
import optparse
import sys
import os.path

from iiif import __version__
from iiif.error import IIIFError
from iiif.static import IIIFStatic, IIIFStaticError


def main():
    """Parse arguments, instantiate IIIFStatic, run."""
    if (sys.version_info < (2, 7)):
        sys.exit("This program requires python version 2.7 or later")

    # Options and arguments
    p = optparse.OptionParser(description='IIIF Image API static file generator',
                              usage='usage: %prog [options] file [[file2..]] (-h for help)',
                              version='%prog ' + __version__)

    p.add_option('--dst', '-d', action='store', default='/tmp',
                 help="Destination directory for images [default '%default']")
    p.add_option('--tilesize', '-t', action='store', type='int', default=512,
                 help="Tilesize in pixels [default %default]")
    p.add_option('--api-version', '--api', '-a', action='store', default='2.1',
                 help="API version, may be 1.1, 2.0 or 2.1 [default %default]")
    p.add_option('--prefix', '-p', action='store', default=None,
                 help="URI prefix for where the images will be served from (default '%default'). "
                      "An empty prefix may be OK if the HTML page including the image shares the "
                      "the same root on the same server as the images, otherwise a full URL should "
                      "be specified. This is used to construct the @id in the info.json")
    p.add_option('--identifier', '-i', action='store', default=None,
                 help="Identifier for the image that will be used in place of the filename "
                      "(minus extension). Notes that this option cannot be used if more than "
                      "one image file is to be processed")
    p.add_option('--extra', '-e', action='append', default=[],
                 help="Extra request parameters to be used to generate static files, may be "
                      "repeated (e.g. '/full/90,/0/default.jpg' for a 90 wide thumnail)")
    p.add_option('--write-html', action='store', default=None,
                 help="Write HTML page to the specified directory using the 'identifier.html' "
                      "as the filename. HTML will launch OpenSeadragon for this image and to "
                      "display some of information about info.json and tile locations. HTML will "
                      "assume OpenSeadragon at relative path openseadragonVVV/openseadragon.min.js "
                      "and user-interface icons in openseadragonVVV/images, where VVV are the "
                      "three parts of the version number. The --include-osd flag is also specified "
                      "then OpenSeadragon will be copied to these locations")
    p.add_option('--include-osd', action='store_true',
                 help="Include OpenSeadragon files with --write-html flag")
    p.add_option('--osd-version', action='store', default='2.0.0',
                 help="Generate static images for older versions of OpenSeadragon. Use of versions "
                      "prior to 1.2.1 will force use of /w,h/ for size parameter instead of /w,/. "
                      "Likely useful only in combination with --api-version=1.1 "
                      "[default %default]")
    p.add_option('--osd-width', action='store', type='int', default='500',
                 help="Width of OpenSeadragon pane in pixels. Applies only with "
                      "--write-html [default %default]")
    p.add_option('--osd-height', action='store', type='int', default='500',
                 help="Height of OpenSeadragon pane in pixels. Applies only with "
                      "--write-html [default %default]")
    p.add_option('--generator', action='store_true', default=False,
                 help="Use named generator modules in iiif.generators package instead "
                      "of a starting image [default %default]")
    p.add_option('--max-image-pixels', action='store', type='int', default=0,
                 help="Set the maximum number of pixels in an image. A non-zero value "
                      "will set a hard limit on the image size. If left unset then the "
                      "default configuration of the Python Image Libary (PIL) will give "
                      "a DecompressionBombWarning if the image size exceeds a default "
                      "maximum, but otherwise continue as normal")
    p.add_option('--dryrun', '-n', action='store_true',
                 help="Do not write anything, say what would be done")
    p.add_option('--quiet', '-q', action='store_true',
                 help="Quite (no output unless there is a warning/error)")
    p.add_option('--verbose', '-v', action='store_true',
                 help="Verbose")

    (opt, sources) = p.parse_args()

    level = logging.DEBUG if (opt.verbose) else \
        logging.WARNING if (opt.quiet) else logging.INFO
    logging.basicConfig(format='%(name)s: %(message)s',
                        level=level)
    logger = logging.getLogger(os.path.basename(__file__))

    if (not opt.write_html and opt.include_osd):
        logger.warn(
            "--include-osd has no effect without --write-html, ignoring")
    if (len(sources) == 0):
        logger.warn("No sources specified, nothing to do, bye! (-h for help)")
    elif (len(sources) > 1 and opt.identifier):
        logger.error(
            "Cannot use --identifier/-i option with multiple sources, aborting.")
    else:
        try:
            sg = IIIFStatic(dst=opt.dst, tilesize=opt.tilesize,
                            api_version=opt.api_version, dryrun=opt.dryrun,
                            prefix=opt.prefix, osd_version=opt.osd_version,
                            generator=opt.generator,
                            max_image_pixels=opt.max_image_pixels,
                            extras=opt.extra)
            for source in sources:
                # File or directory (or neither)?
                if (os.path.isfile(source) or opt.generator):
                    logger.info("source file: %s" % (source))
                    sg.generate(source, identifier=opt.identifier)
                    if (opt.write_html):
                        sg.write_html(html_dir=opt.write_html, include_osd=opt.include_osd,
                                      osd_width=opt.osd_width, osd_height=opt.osd_height)
                elif (os.path.isdir(source)):
                    logger.warn(
                        "Ignoring source '%s': directory coversion not supported" % (source))
                else:
                    logger.warn(
                        "Ignoring source '%s': neither file nor path" % (source))
        except (IIIFStaticError, IIIFError) as e:
            # catch known errors and report nicely...
            logger.error("Error: " + str(e))

if __name__ == '__main__':
    main()
