# IIIF OpenSeadragon Authentication Test

A copy of OpenSeadragon must be added to this directory
Plus build the collections branch of openseadragon and copy the openseadragon build directory to this directory.

## Running demo

The demo page `index.html` assumes that an IIIF server is running at `http://localhost:8001` with the image `http://localhost:8001/tetons` (see /server in this repository). Running a simply python webserver from this (`demo-auth`) directory with `python -m SimpleHTTPServer` will generate the following on access to <http://localhost:8000/>:

```sh
simeon@RottenApple demo-auth>python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
127.0.0.1 - - [27/Nov/2015 11:14:38] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /rob_stanford_google.html HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/openseadragon.min.js HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /jquery-1.11.1.min.js HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/images/zoomin_rest.png HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/images/zoomin_grouphover.png HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/images/zoomin_hover.png HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/images/zoomin_pressed.png HTTP/1.1" 200 -
127.0.0.1 - - [27/Nov/2015 11:14:43] "GET /openseadragon121/images/zoomout_rest.png HTTP/1.1" 200 -
...
```

The initial image will be degraded (no zoom) but a login button will be displayed in the lower left. Once auth'zed, a zoomable image will be displayed.

## OpenSeadragon versions

At present this demonstration works only with OpenSeadragon < 2.0, latest is 1.2.1. With OpenSeadragon 2.0.0 the error message `Unable to open [object Object]: Unable to load TileSource` is displayed.

## Issues with demo

  1. At present this demo has hard-coded the `/token` URI. It should instead have only the URI of the non-degrated image information. 
  2. It seems that osd makes and OPTIONS request after auth and if this isn't right then it won't work. Is it possible to make this non-critical?
  3. Demo client does not look for our use optional clientId service
