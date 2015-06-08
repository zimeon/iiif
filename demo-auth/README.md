# IIIF OpenSeadragon Authentication Test

A copy of OpenSeadragon must be added to this directory
Plus build the collections branch of openseadragon and copy the openseadragon build directory to this directory.

## Running demo

The demo page `index.html` assumes that an IIIF server is running at `http://localhost:8001` with the image `http://localhost:8001/tetons` (see /server in this repository). Running a simply python webserver from this (`osd`) directory with `python -m SimpleHTTPServer` will generate the following on access to <http://localhost:8000/>:

```sh
simeon@Cider osd>python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/openseadragon.min.js HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /jquery-1.11.1.min.js HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomin_rest.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomin_grouphover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomin_hover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomin_pressed.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomout_rest.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomout_grouphover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/home_grouphover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomout_hover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/fullpage_pressed.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/fullpage_grouphover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/zoomout_pressed.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/home_hover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/fullpage_rest.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/home_rest.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/home_pressed.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /openseadragon/images/fullpage_hover.png HTTP/1.1" 200 -
127.0.0.1 - - [03/Jun/2015 13:00:14] "GET /favicon.ico HTTP/1.1" 200 -
```

The initial image will be degraded (no zoom) but a login button will be displayed in the lower left. Once auth'zed, a zoomable image will be displayed.

## OpenSeadragon versions

At present this demonstration works only with OpenSeadragon < 2.0, latest is 1.2.1. With OpenSeadragon 2.0.0 the error message `Unable to open [object Object]: Unable to load TileSource` is displayed.

## Issues with demo

  1. At present this demo has hard-coded the `/token` URI. It should instead have only the URI of the non-degrated image information. 
  2. It seems that osd makes and OPTIONS request after auth and if this isn't right then it won't work. Is it possible to make this non-critical?
  3. Demo client does not look for our use optional clientId service
