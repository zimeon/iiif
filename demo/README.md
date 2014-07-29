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
described in *Manual installation* in <https://github.com/zimeon/iiif>, 
the `python setup.py build` and `sudo python setup.py install` steps are 
not necessary unless you want to rebuild the tiles). 
All of the static files for the demo are included in git so you can run 
OpenSeadragon immediately. Instructions for regenerating them are below 
and allow testing with different tile size or with different images.

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

Bugs
----

For some small tiles sizes the static tile generator does no make the right size. For example, with the tetons image, OSD requests `/demo/tetons/full/32,24/0/native.jpg` for a very low-res whole image. The static file generator uses different rounding and generates `/demo/tetons/full/31,23/0/native.jpg` instead.

There appears to be a bug in OSD the results in multiple requests for the same image at very small sizes. For example, when viewing the starfish2 image, OSD makes the following sequence of requests for a 1x1 image:

```
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] code 404, message File not found
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] "GET /demo/starfish2/full/1,1/0/native.jpg HTTP/1.1" 404 -
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] code 404, message File not found
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] "GET /demo/starfish2/full/1,1/0/native.jpg HTTP/1.1" 404 -
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] code 404, message File not found
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] "GET /demo/starfish2/full/1,1/0/native.jpg HTTP/1.1" 404 -
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] code 404, message File not found
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] "GET /demo/starfish2/full/1,1/0/native.jpg HTTP/1.1" 404 -
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] code 404, message File not found
1.0.0.127.in-addr.arpa - - [29/Jul/2014 15:25:30] "GET /demo/starfish2/full/1,1/0/native.jpg HTTP/1.1" 404 -
```

