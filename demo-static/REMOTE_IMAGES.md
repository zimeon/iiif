# IIIF Using Static Files on a Remote Server

The trivial demonstration described in [README.md] assumes that the HTML page, OpenSeadragon, and the image tiles are located on the same server. In many production instances this will not be the case. Static files still work over separate servers but there are a coupd of issues that need to be taken into account. First, here is a possible set of commands to build tiles, image information, a test HTML page for the image testimages/tetons.jpg, and then copy the files to two different servers:

```
# Clean out directories in case we try this several times
rm -rf /tmp/iiif_static2_html /tmp/iiif_static2_img

# Build all files, include OpenSeadragon
./iiif_static.py --api-version 2.0 -d /tmp/iiif_static2_img -p http://resync.library.cornell.edu/tmp/iiif_static2 --write-html /tmp/iiif_static2_html --include-osd testimages/tetons.jpg

# Copy HTML to one server
rsync -av --delete /tmp/iiif_static2_html/ simeon@zimeon.com:www/tmp/iiif_static2/

# Copy tiles and info.json to another server
rsync -av --delete /tmp/iiif_static2_img/ sw272@resync.library.cornell.edu:htdocs-resync/tmp/iiif_static2/

# Can now access http://zimeon.com/tmp/iiif_static2/tetons.html
```

## Gotcha 1: CORS header

If the Image Information (`info.json`) and tiles (which must be on the same server as the `info.json`) are on a different server than the HTML page then the browser will only allow the `info.json` to be loaded with the correct CORS header. Without it the browser will reject the load request. For example, the following is the error shown in the Chrome JavaScript console:
 
```
XMLHttpRequest cannot load http://resync.library.cornell.edu/tmp/iiif_static2/tetons/info.json. No 'Access-Control-Allow-Origin' header is present on the requested resource. Origin 'http://zimeon.com' is therefore not allowed access.
```

Within [Apache the appropriate command](http://enable-cors.org/server_apache.html) to add a CORS header to permit access from anywhere is:

```
Header set Access-Control-Allow-Origin "*"
```

and then with this setting we see the `Access-Control-Allow-Origin` header:

```
simeon@RottenApple iiif>curl -I http://resync.library.cornell.edu/tmp/iiif_static2/tetons/info.json
HTTP/1.1 200 OK
Date: Thu, 23 Jul 2015 14:12:31 GMT
Server: Apache/2.2.15 (Red Hat)
Last-Modified: Thu, 23 Jul 2015 12:59:35 GMT
ETag: "8409d2-1fe-51b8a758a7bc0"
Accept-Ranges: bytes
Content-Length: 510
Access-Control-Allow-Origin: *
Connection: close
Content-Type: application/json
```
