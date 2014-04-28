IIIF Image API Static File Demo with OpenSeadragon
==================================================

A copy of OpenSeadragon is included in the the `demo/osd` directory
for convenience. The current version may be downloaded from 
<http://openseadragon.github.io/#download>.

To remove and regenerate tiles and `info.json` files:
```
iiif> rm -rf demo/tetons demo/starfish demo/starfish2

iiif> bin/iiif_static.py -d demo/tetons testimages/tetons.jpg
iiif> bin/iiif_static.py -d demo/starfish -t 1024 testimages/starfish.jpg
iiif> bin/iiif_static.py -d demo/starfish2 -t 256 testimages/starfish2.jpg
```

Run test server on local machine from `iiif` directory:
```bash
iiif> python -m SimpleHTTPServer
```

And then access <http://localhost:8000/demo/index.html>.

