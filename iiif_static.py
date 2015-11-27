#!/usr/bin/env python
"""iiif_static: Generate static images implementing the IIIF Image API level 0.

Copyright 2014,2015 Simeon Warner
"""

import logging
import optparse
import sys
import os.path

from iiif import __version__
from iiif.static import IIIFStatic

def main():
    """Parse arguments, instantiate IIIFStatic, run."""
    if (sys.version_info < (2,6)):
        sys.exit("This program requires python version 2.6 or later")

    # Options and arguments
    p = optparse.OptionParser(description='IIIF Image API static file generator',
                              usage='usage: %prog [options] file [[file2..]] (-h for help)',
                              version='%prog '+__version__ )

    p.add_option('--dst', '-d', action='store', default='/tmp',
                 help="destination directory [default '%default']")
    p.add_option('--tilesize', '-t', action='store', type='int', default=512,
                 help="tilesize in pixels [default %default]")
    p.add_option('--api-version', '--api','-a', action='store', default='2.0',
                 help="API version, may be 1.1 or 2.0 [default %default]")
    p.add_option('--prefix', '-p', action='store', default=None,
                 help="URI prefix for where the images will be served from (default '%default'). "
                      "An empty prefix may be OK if the HTML page including the image shares the "
                      "the same root on the same server as the images, otherwise a full URL should "
                      "be specified. This is used to construct the @id in the info.json")
    p.add_option('--identifier', '-i', action='store', default=None,
                 help="Identifier for the image that will be used in place of the filename "
                      "(minus extension). Notes that this option cannot be used if more than "
                      "one image file is to be processed")
    p.add_option('--write-html', action='store', default=None,
                 help="Write HTML page to the specified directory using the 'identifier.html' "
                      "as the filename. HTML will launch OpenSeadragon for this image and to "
                      "display some of information about info.json and tile locations. HTML will "
                      "assume OpenSeadragon at relative path osd/openseadragon.min.js and interface "
                      "icons in osd/images. The --include-osd flag is also specified then "
                      "OpenSeadragon will be copied to these locations")
    p.add_option('--include-osd', action='store_true',
                 help="Include OpenSeadragon files with --write-html flag")
    p.add_option('--osd1', action='store_true',
                 help="Generate static images for OSD v1.1 rather than v2.x. Uses /w,h/ for size "
                      "parameter instead of /w,/. Likely useful only in combination with "
                      "--api-version=1.1")
    p.add_option('--dryrun', '-n', action='store_true',
                 help="do not write anything, say what would be done")
    p.add_option('--verbose', '-v', action='store_true',
                 help="verbose")

    (opt, sources) = p.parse_args()

    logging.basicConfig( format='%(name)s: %(message)s',
                         level=( logging.INFO if (opt.verbose) else logging.WARNING ) )
    logger = logging.getLogger(os.path.basename(__file__))

    if (len(sources)==0):
        logger.warn("No sources specified, nothing to do, bye! (-h for help)")
    elif (len(sources)>1 and opt.identifier):
        logger.warn("Cannot use --identifier/-i option with multiple sources, aborting.")
    else:
        sg = IIIFStatic( dst=opt.dst, tilesize=opt.tilesize,
                         api_version=opt.api_version, dryrun=opt.dryrun,
                         prefix=opt.prefix, osd_version1=opt.osd1 )
        for source in sources:
            # File or directory (or neither)?
            if (os.path.isfile(source)):
                logger.info("source file: %s" % (source))
                sg.generate(source, identifier=opt.identifier)
                if (opt.write_html):
                    sg.write_html(opt.write_html,opt.include_osd,opt.os1)
            elif (os.path.isdir(source)):
                logger.warn("Ignoring source '%s': directory coversion not supported" % (source))
            else:
                logger.warn("Ignoring source '%s': neither file nor path" % (source))

if __name__ == '__main__':
    main()
