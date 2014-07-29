IIIF Image API Static File Demo with OpenSeadragon
==================================================

The [IIIF Image API](http://iiif.io/api/image) supports description of
tiles that may be implemented using static files. This demo
uses static files to drive [OpenSeadragon](http://openseadragon.github.io/).
(At present the viewers available, such as OpenSeadragon, need specific 
tile sizes to be available based on knowledge of the viewer. Later 
revisions of the Image API and viewers will reduce or eliminate the
amount of out-of-band knwoledge required.)

To run this demo you will need a copy of this git repository (clone as 
described in <https://github.com/zimeon/iiif>). All of the static files for the demo are 
included in git so you can run OpenSeadragon immediately. Instructions
for regenerating them are below and allow testing with different tile
size or with different images.

A copy of OpenSeadragon is included in the the `demo/osd` directory
for convenience. The current version may be downloaded from 
<http://openseadragon.github.io/#download>.

Run demo
--------

Run a test web server on local machine from `iiif` directory:
```
iiif> python -m SimpleHTTPServer
```

And then access <http://localhost:8000/demo/index.html>.

Regerating tiles
----------------

To remove and regenerate tiles and `info.json` files:
```
iiif> rm -rf demo/tetons demo/starfish demo/starfish2

iiif> bin/iiif_static.py -d demo/tetons testimages/tetons.jpg
iiif> bin/iiif_static.py -d demo/starfish -t 1024 testimages/starfish.jpg
iiif> bin/iiif_static.py -d demo/starfish2 -t 256 testimages/starfish2.jpg
```

Storage space
-------------

How big are the complete sets of tiles and `info.json`? From initial tests
it seems that the tilesets are actually smaller that the original image though 
I suspect this is to do with default quality of the Python Image Library
output jpegs.

```
iiif> du -sh testimages/tetons.jpg demo/tetons testimages/starfish.jpg demo/starfish testimages/starfish2.jpg demo/starfish2
2.8M		   testimages/tetons.jpg
1.8M		   demo/tetons
3.4M		   testimages/starfish.jpg
2.9M		   demo/starfish
2.7M		   testimages/starfish2.jpg
2.0M		   demo/starfish2
```
