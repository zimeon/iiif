## RHEL 6.6

### Pillow and image libraries

See <http://pillow.readthedocs.org/en/latest/installation.html>

Install libraries:

```
sudo yum install libtiff-devel libjpeg-devel libzip-devel freetype-devel \
    lcms2-devel libwebp-devel tcl-devel tk-devel
```

For JPEG2000 support the RedHat `openjpeg` libraries are too old to be supported by 
Pillow -- they are 1.3 and Pillow requires 2.0 or 2.1. Thus if JPEG2000 support
is required then the `openjpeg` libraries must be installed from elsewhere. This is
very easy direct from the 
[`openjpeg` github site](https://github.com/uclouvain/openjpeg). Compilation requires
`cmake` which is available from RedHat:

```
sudo yum install cmake
git clone git@github.com:uclouvain/openjpeg.git
cd openjpeg/
cmake -DCMAKE_INSTALL_PREFIX=/usr .
make
sudo make install

## Problem with install using openjpeg libraries is that when PIL (Pillow) is loaded
## by Python it can't find the openjpeg libraries (either in default /usr/local/lib 
## or /usr/lib as with -D flag above). Ugly fix is to set LD_LIBRARY_PATH for the 
## environment running the code. Should be a way around this though...

export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH
```

Can then install `Pillow`:

```
sudo pip install Pillow
```

Pillow should then support all the image formats we need (including JPEG2000 if `openjpeg` 
was installed. The image formats are displayed in a table at then end of the install:

```
--------------------------------------------------------------------
    PIL SETUP SUMMARY
    --------------------------------------------------------------------
    version      Pillow 2.9.0
    platform     linux2 2.6.6 (r266:84292, Nov 21 2013, 10:50:32)
                 [GCC 4.4.7 20120313 (Red Hat 4.4.7-4)]
    --------------------------------------------------------------------
    *** TKINTER support not available
    --- JPEG support available
    --- OPENJPEG (JPEG2000) support available (2.1)
    --- ZLIB (PNG/ZIP) support available
    --- LIBTIFF support available
    --- FREETYPE2 support available
    --- LITTLECMS2 support available
    --- WEBP support available
    --- WEBPMUX support available
    --------------------------------------------------------------------
    To add a missing option, make sure you have the required
    library, and set the corresponding ROOT variable in the
    setup.py script.
    
    To check the build, run the selftest.py script.
```

(If `openjpeg` libraries were not installed then there will be a `***`
on the line for JPEG2000 support but everything else will work fine.)

## RHEL 6.5

Was same as RHEL 6.6 above. When I did this in 2014 the current version 
of Pillow was 2.6.0. Did not try compiling `openjpeg` libraries for JPEG2000
support.
