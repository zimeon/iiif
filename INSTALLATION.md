## RHEL 6.5

### Pillow and image libraries

See <http://pillow.readthedocs.org/en/latest/installation.html>

Install libraries:

```
sudo yum install libtiff-devel libjpeg-devel libzip-devel freetype-devel \
    lcms2-devel libwebp-devel tcl-devel tk-devel
```

Can then install `Pillow` and will get everything we need except openjpeg:

```
    --------------------------------------------------------------------
    PIL SETUP SUMMARY
    --------------------------------------------------------------------
    version      Pillow 2.6.0
    platform     linux2 2.6.6 (r266:84292, Nov 21 2013, 10:50:32)
                 [GCC 4.4.7 20120313 (Red Hat 4.4.7-4)]
    --------------------------------------------------------------------
    *** TKINTER support not available
    --- JPEG support available
    *** OPENJPEG (JPEG2000) support not available
    --- ZLIB (PNG/ZIP) support available
    --- LIBTIFF support available
    --- FREETYPE2 support available
    --- LITTLECMS2 support available
    *** WEBP support not available
    *** WEBPMUX support not available
    --------------------------------------------------------------------
```

??? Have tried installing openjpeg but this doesn't seem to be 
picked up by Pillow when I install:

```
sw272@sw272-dev iiif>sudo yum install openjpeg openjpeg-devel openjpeg-libs
Setting up Install Process
Package openjpeg-1.3-10.el6_5.x86_64 already installed and latest version
Package openjpeg-devel-1.3-10.el6_5.x86_64 already installed and latest version
Package openjpeg-devel-1.3-10.el6_5.i686 already installed and latest version
Package openjpeg-libs-1.3-10.el6_5.x86_64 already installed and latest version
Package openjpeg-libs-1.3-10.el6_5.i686 already installed and latest version
```

seems that Pillow needs a newer version: "Pillow has been tested with openjpeg 2.0.0 and 2.1.0."