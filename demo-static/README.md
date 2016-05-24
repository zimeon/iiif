IIIF Image API Static File Demo with OpenSeadragon
==================================================

The [IIIF Image API](http://iiif.io/api/image) supports description of
tiles that may be implemented using static files that provide 
[level 0 compliance](http://iiif.io/api/image/2.0/compliance). This demo
uses static files to drive [OpenSeadragon](http://openseadragon.github.io/).
(At present the viewers available, such as OpenSeadragon, need specific 
tile sizes to be available based on knowledge of the viewer. Later 
revisions of the Image API and viewers will reduce or eliminate the
amount of out-of-band knwoledge required.)

To run this demo you will need a copy of this git repository (clone as 
described in *Manual installation* in <https://github.com/zimeon/iiif>, 
the `python setup.py build` and `sudo python setup.py install` steps are 
not necessary unless you want to rebuild the tiles). 
All of the static files for the demo and the OpenSeadragon code are 
included in git so you can run the demo immediately. Instructions for 
regenerating them are below and allow testing with different tile sizes,
with different images, or with different Image API and OpenSeadragon
versions.

A copy of OpenSeadragon v2.0 is included in the the `iiif/third_party/openseadragon200`
directory for convenience. The current version may be downloaded from 
<http://openseadragon.github.io/#download>.

Run demo
--------

Run a test web server on local machine from `iiif` directory:
```
iiif> python -m SimpleHTTPServer
```

And then access <http://localhost:8000/demo-static/index.html>.

Regerating tiles
----------------

To remove and regenerate tiles and `info.json` files:
```
iiif> rm -rf demo-static/tetons demo-static/tetons.html; ./iiif_static.py --write-html demo-static -d demo-static --api-version=1.1 testimages/tetons.jpg

iiif> rm -rf demo-static/starfish demo-static/starfish.html; ./iiif_static.py --write-html demo-static -d demo-static -t 1024 testimages/starfish.jpg

iiif> rm -rf demo-static/starfish2 demo-static/starfish2.html; ./iiif_static.py --write-html demo-static -d demo-static -t 200 --osd-version=1.2.1 --osd-width=200 --osd-height=200 testimages/starfish2.jpg
```

Storage space
-------------

How big are the complete sets of tiles and `info.json`? From initial tests
it seems that the tilesets are actually smaller that the original image though 
I suspect this is to do with default quality of the Python Image Library
output jpegs.

```
iiif> du -sh testimages/tetons.jpg demo-static/tetons testimages/starfish.jpg demo-static/starfish testimages/starfish2.jpg demo-static/starfish2
2.8M		   testimages/tetons.jpg
1.8M		   demo-static/tetons
3.4M		   testimages/starfish.jpg
2.9M		   demo-static/starfish
2.7M		   testimages/starfish2.jpg
2.0M		   demo-static/starfish2
```
