iiif changelog
==============

2016-05-xx v1.0.0
- Change to 1.x.x version as core codebase stable
- Make IIIF Image API v2.1 the default (although not all features implemented)
- Improvements for PIL manipulator (thanks @jgreidy)
- Extended info.profile to complex profiles for 2.x Image Information 

2016-04-22 v0.6.1
- Now works with python 2.6, 2.7, 3.3, 3.4 and 3.5
- Static tile generation supports both use of canonical size syntax for
  OpenSeadragon >= 1.2.1, and the old syntax for earlier versions
- Better surface/handle image size warnings from Pillow
- Use logging instead of print in iiif.static

2015-08-17 v0.6.0
- Refactor manipulators for easier testing
- Improve test coverage of PIL manipulator
- Fix static files tile sizes (thanks @edsu)
- Modify static tile generation for canonical URIs as used by OpenSeadragon 2.0
- Test server now a Flask application
- DRAFT - IIIF API v2.1 features for testing (not final), add /square/ 
  region, and trial authentication support

2015-02-14 v0.5.1
- Valentines edition, wishing Amy and Ian lasting happiness
- PIL and netpbm manipulators support IIIF API v2.0 and v1.1 at level 2
- Improved test coverage using IIIF validator
  (https://pypi.python.org/pypi/iiif-validator)

2014-11-11 v0.5.0
- Supports IIIF API v2.0 and v1.1 at level 1

2014-09-17 v0.4.2
- Tidy tests, checked against python 2.6 and 2.7
- Still needs work to support recently released IIIF API v2.0

2014-04-28 v0.4.1
- Add iiif_static.py as script for pypi install

2014-04-28 v0.4.0
- Aim to support IIIF API v1.1 and v2.0
- Added generation of static file tiles for OpenSeadragon
- Included demo for OpenSeadragon with static file tiles

2014-04-22 v0.3.0
- Change pypi package name from i3f to iiif

2013-05-21 v0.2.0
- Reorganized, aims for IIIF API v1.0
  (http://www-sul.stanford.edu/iiif/image-api/)
- PIL library support (IIIFManipulatorPIL) and null tested, the netpbm
  version (IIIFManipulatorNetpbm) has not been updated/tested and is
  likely broken.
- Designed to work with Loris for for Open Seadragon demo
  (https://github.com/zimeon/loris)
- Add GPL

2012-03-21 v0.1.0
- First stab at IIIF API v0.1
