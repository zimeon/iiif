#!/usr/bin/env python
"""
iiif_static: Generate static images implementing the IIIF Image API level 0

Copyright 2014 Simeon Warner

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License
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

    p.add_option('--dst', '-d', action='store',
                 help="destination directory")
    p.add_option('--tilesize', '-t', action='store', type='int',
                 help="tilesize in pixels")
    p.add_option('--dryrun', '-n', action='store_true',
                 help="do not write anything, say what would be done")
    p.add_option('--verbose', '-v', action='store_true',
                 help="verbose")

    (args, sources) = p.parse_args()

    logging.basicConfig( format='%(message)s',
                         level=( logging.INFO if (args.verbose) else logging.WARNING ) )

    for source in sources:
        # File or directory (or neither)?
        sg = IIIFStatic(dst=args.dst,tilesize=args.tilesize)
        if (os.path.isfile(source)):
            print "source file: %s" % (source)
            sg.generate(source)
        elif (os.path.isdir(source)):
            print "source dir: %s - FIXME: not yet supported" % (source)
        else:
            print "ignoring source '%s': neither file nor path" % (source)

if __name__ == '__main__':
    main()
