"""Implementation of IIIF image manipulations using netpbm programs

FIXME - has not been kept up to date with other code
"""

import re
import os
import os.path
import glob
import subprocess

from error import IIIFError
from request import IIIFRequest
from manipulator import IIIFManipulator

class IIIFManipulatorNetpbm(IIIFManipulator):
    """Module to manipulate and image according to iiif rules

    All exceptions are raise as Error objects which directly
    determine the HTTP response.
    """

    tmpdir = '/tmp'
    filecmd = None
    pnmdir = None

    def __init__(self):
        super(IIIFManipulatorNetpbm, self).__init__()
        self.complianceLevel="http://iiif.example.org/compliance/level/1"
        if (self.filecmd is None):
            self.find_binaries()

    @classmethod
    def find_binaries(cls,tmpdir=None,shellsetup=None,filecmd=None,pnmdir=None):
        """Set instance vars for directory and binar locations

        FIXME - should accept params to set things other than defaults
        """
        cls.tmpdir = ( '/tmp' if (tmpdir is None) else tmpdir)
        # Shell setup command (e.g set library path)
        cls.shellsetup = ( '' if (shellsetup is None) else shellsetup)
        cls.filecmd = ( '/usr/bin/file' if (filecmd is None) else filecmd)
        if (pnmdir is None):
            cls.pnmdir = '/usr/bin'
            for dir in ('/usr/local/bin','/sw/bin'):
                if (os.path.isfile(os.path.join(dir,'pngtopnm'))):
                    cls.pnmdir=dir
        else:
            cls.pnmdir=pnmdir
        # Recklessly assume everything else under cls.pnmdir
        cls.pngtopnm  = os.path.join( cls.pnmdir , 'pngtopnm' )
        cls.pnmfile   = os.path.join( cls.pnmdir , 'pnmfile' )
        cls.pnmcut    = os.path.join( cls.pnmdir , 'pnmcut' )
        cls.pnmscale  = os.path.join( cls.pnmdir , 'pnmscale' )
        cls.pnmrotate = os.path.join( cls.pnmdir , 'pnmrotate' )
        cls.pnmflip   = os.path.join( cls.pnmdir , 'pnmflip' )
        cls.pnmtopng  = os.path.join( cls.pnmdir , 'pnmtopng' )
        cls.ppmtopgm  = os.path.join( cls.pnmdir , 'ppmtopgm' )
        cls.pnmtotiff = os.path.join( cls.pnmdir , 'pnmtotiff' )
        cls.pnmtojpeg = os.path.join( cls.pnmdir , 'pnmtojpeg' )
        cls.pamditherbw = os.path.join( cls.pnmdir , 'pamditherbw' )
        # Need djatoka to get jp2 output
        cls.djatoka_comp = '/Users/simeon/packages/adore-djatoka-1.1/bin/compress.sh'

    def do_first(self):
        pid = os.getpid()
        self.basename = os.path.join(self.tmpdir,'iiif_netpbm_'+str(pid))
        outfile = self.basename+'.pnm'
        # Convert source file to pnm
        filetype = self.file_type(self.srcfile)
        if (filetype == 'png'):
            #print "doing png->pnm"
            #print self.pngtopnm+' '+self.srcfile+' > '+outfile
            if (self.shell_call(self.pngtopnm+' '+self.srcfile+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pngtopnm.")
        else:
            raise IIIFError(code='501',
                           text='bad input file format')
        self.tmpfile = outfile

    def do_region(self):
        infile = self.tmpfile
        outfile = self.basename+'.reg'
        # Get size
        (self.width,self.height)=self.image_size(infile)
        # Region
        #simeon@ice ~>cat m.pnm | pnmcut 10 10 100 200 > m1.pnm
        (x,y,w,h)=self.region_to_apply()
        if (x is None):
            #print "region: full"
            self.tmpfile = infile
        else:
            #print "region: (%d,%d,%d,%d)" % (x,y,w,h)
            if (self.shell_call('cat '+infile+' | '+self.pnmcut+' '+str(x)+' '+str(y)+' '+str(w)+' '+str(h)+'  > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmcut.")
            self.width=w
            self.height=h
            self.tmpfile = outfile

    def do_size(self):
        # Size
        # simeon@ice ~>cat m1.pnm | pnmscale -width 50 > m2.pnm
        infile = self.tmpfile
        outfile = self.basename+'.siz'
        (w,h)=self.size_to_apply()
        if (w is None):
            #print "size: no scaling"
            self.tmpfile=infile
        else:
            #print "size: scaling to (%d,%d)" % (w,h)
            if (self.shell_call('cat '+infile+' | '+self.pnmscale+' -width '+str(w)+' -height '+str(h)+'  > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmscale.")
            width=w
            height=h
            self.tmpfile=outfile

    def do_rotation(self):
        infile = self.tmpfile
        outfile = self.basename+'.rot'
        # Rotate
        #simeon@ice ~>cat m2.pnm | pnmrotate 123.456 > m3.pnm
        #pnmrotate: angle must be between -90 and 90 and it is CCW not CW
        rot=self.rotation_to_apply()
        if (rot==0.0):
            #print "rotation: no rotation"
            self.tmpfile=infile
        elif (rot<=90.0 or rot>=270.0):
            if (rot>=270.0):
                rot-=360.0
            #print "rotation: by %f degrees clockwise" % (rot)
            if (self.shell_call('cat '+infile+' | '+self.pnmrotate+' -background=#FFF '+str(-rot)+'  > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmrotate.")
            self.tmpfile=outfile
        else:
            # Between 90 and 270 = flip and then -90 to 90
            rot-=180.0
            #print "rotation: by %f degrees clockwise" % (rot)
            if (self.shell_call('cat '+infile+' | '+self.pnmflip+' -rotate180 | '+self.pnmrotate+' '+str(-rot)+'  > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmrotate.")
            self.tmpfile=outfile

    def do_quality(self):
        infile = self.tmpfile
        outfile = self.basename+'.col'
        # Quality (bit-depth):
        quality=self.quality_to_apply()
        if (quality == 'grey'):
            #print "quality: grey"
            if (self.shell_call('cat '+infile+' | '+self.ppmtopgm+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from ppmtopgm.")
            self.tmpfile=outfile
        elif (quality == 'bitonal'):
            #print "quality: grey"
            if (self.shell_call('cat '+infile+' | '+self.ppmtopgm+' | '+self.pamditherbw+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from ppmtopgm.")
            self.tmpfile=outfile
        elif (quality == 'quality'):
            #print "quality: quality"
            self.tmpfile=infile
        else: 
            raise IIIFError(code=400,parameter='quality',
                           text="Unknown quality parameter value requested.")

    def do_format(self):
        infile = self.tmpfile
        outfile = self.basename+'.out'
        outfile_jp2 = self.basename+'.jp2'
        # Now convert finished pnm file to output format
        #simeon@ice ~>cat m3.pnm | pnmtojpeg  > m4.jpg
        #simeon@ice ~>cat m3.pnm | pnmtotiff > m4.jpg
        #pnmtotiff: computing colormap...
        #pnmtotiff: Too many colors - proceeding to write a 24-bit RGB file.
        #pnmtotiff: If you want an 8-bit palette file, try doing a 'ppmquant 256'.
        #simeon@ice ~>cat m3.pnm | pnmtopng  > m4.png
        fmt = ( 'png' if (self.request.format is None) else self.request.format)
        if (fmt == 'png'):
            #print "format: png"
            if (self.shell_call(self.pnmtopng+' '+infile+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmtopng.")
            mime_type="image/png"
        elif (fmt == 'tiff' or fmt == 'jp2'):
            #print "format: tiff/jp2"
            if (self.shell_call(self.pnmtotiff+' '+infile+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmtotiff.")
            mime_type="image/tiff"
            if (fmt == 'jp2'):
                # use djatoka after tiff
                if (self.shell_call(DJATOKA_COMP+' -i '+outfile+' -o '+outfile_jp2)):
                    raise IIIFError(text="Oops... got nonzero output from DJATOKA_COMP.")
                mime_type="image/jp2"
                outfile=tmpfile_jp2
        elif (fmt == 'jpg'):
            #print "format: jpg"
            if (self.shell_call(self.pnmtojpeg+' '+infile+' > '+outfile)):
                raise IIIFError(text="Oops... got nonzero output from pnmtojpeg.")
            mime_type="image/jpeg"
        else:
            raise IIIFError(code=415, parameter='format',
                           text="Unsupported output file format (%s), only png,jpg,tiff are supported."%(fmt))
        self.outfile=outfile
        self.output_format=fmt
        self.mime_type=mime_type

    def file_type(self,file):
        return('png')
        pout = os.popen(self.filecmd+' '+file,'r')
        fileout=pout.read(200)
        pout.close()
        #print "file output = " + fileout
        if (re.search('PNG image data',fileout)):
            return('png')
        # failed
        return(None)

    def image_size(self,pnmfile):
        """Get width and height of pnm file

        simeon@homebox src>pnmfile /tmp/214-2.png
        /tmp/214-2.png:PPM raw, 100 by 100  maxval 255
        """
        pout = os.popen(self.shellsetup+self.pnmfile+' '+pnmfile,'r')
        pnmfileout=pout.read(200)
        pout.close()
        m=re.search(', (\d+) by (\d+) ',pnmfileout);
        if (m is None):
            raise IIIFError(text="Bad output from pnmfile when trying to get size.")
        w=int(m.group(1))
        h=int(m.group(2))
        #print "pnmfile output = %s" % (pnmfileout)
        #print "image size = %d,%d" % (w,h)
        return(w,h)

    def shell_call(self,shellcmd):
        """Shell call with necessary setup first"""
        return(subprocess.call(self.shellsetup+shellcmd,shell=True))

    def cleanup(self):
        """Clean up any temporary files"""
        for file in glob.glob(self.basename+'*'):
            os.unlink(file)
