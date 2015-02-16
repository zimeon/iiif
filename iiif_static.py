#!/usr/bin/env python
"""
iiif_static: Generate static images implementing the IIIF Image API level 0

Copyright 2014 Simeon Warner
"""

import logging
import optparse
import sys
import os.path 

from iiif import __version__
from iiif.static import IIIFStatic

def main():

    if (sys.version_info < (2,6)):
        sys.exit("This program requires python version 2.6 or later")
    
    # Options and arguments
    p = optparse.OptionParser(description='IIIF Image API static file generator',
                              usage='usage: %prog [options] file|path (-h for help)',
                              version='%prog '+__version__ )

    p.add_option('--dst', '-d', action='store', default='/tmp',
                 help="destination directory [/tmp default]")
    p.add_option('--tilesize', '-t', action='store', type='int', default=512,
                 help="tilesize in pixels [512 default]")
    p.add_option('--api-version', '--api','-a', action='store', default='1.1',
                 help="API version, may be 1.1 [default] or 2.0") 
    p.add_option('--dryrun', '-n', action='store_true',
                 help="do not write anything, say what would be done")
    p.add_option('--verbose', '-v', action='store_true',
                 help="verbose")

    (args, sources) = p.parse_args()

    logging.basicConfig( format='%(name)s: %(message)s',
                         level=( logging.INFO if (args.verbose) else logging.WARNING ) )
    logger = logging.getLogger(os.path.basename(__file__))

    if (len(sources)==0):
        logger.warn("no sources specified, nothing to do, bye! (-h for help)")
    else:
        for source in sources:
            # File or directory (or neither)?
            sg = IIIFStatic( dst=args.dst, tilesize=args.tilesize,
                             api_version=args.api_version, dryrun=args.dryrun )
            if (os.path.isfile(source)):
                logger.info("source file: %s" % (source))
                sg.generate(source)
            elif (os.path.isdir(source)):
                raise Exception("source dir: %s - FIXME: not yet supported" % (source))
            else:
                logger.warn("ignoring source '%s': neither file nor path" % (source))

if __name__ == '__main__':
    main()
