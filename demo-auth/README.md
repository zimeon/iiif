# IIIF OpenSeadragon Authentication Test

## Running the demos locally

In order to simulate client and server on different servers, we run the client pages on port 8000 and the test image server on port 8001.

### Starting the image server

In one window, change to root of the checked out repository (parent dir of this dir) and run:

```sh
(py2) iiif> ./iiif_testserver.py -p 8001 --auth
Installing pil IIIFManipulator at /1.0_pil/ v1.0 none
Installing pil IIIFManipulator at /1.1_pil/ v1.1 none
Installing pil IIIFManipulator at /2.0_pil/ v2.0 none
Installing pil IIIFManipulator at /2.1_pil/ v2.1 none
Installing pil IIIFManipulator at /2.1_pil_gauth/ v2.1 gauth
Installing pil IIIFManipulator at /2.1_pil_basic/ v2.1 basic
Installing pil IIIFManipulator at /2.1_pil_clickthrough/ v2.1 clickthrough
Installing pil IIIFManipulator at /2.1_pil_kiosk/ v2.1 kiosk
Starting test server on http://localhost:8001/ ...
...
(will then show log lines for any access)
```

You can test that the image server is running by accessing <http://localhost:8001/> and it should respond with a web page listing Image API versions and auth types with the title **iiif_testserver on localhost:8001**. Leave this window open.

## Starting a server for the demo pages

In another window, run a simple python webserver from this (`demo-auth`) directory. For Python2 you can use:

```
python -m SimpleHTTPServer
```

with Python3 you can use:

```
python3 -m http.server
```

Taking the Python2 example, the following launches a server accessible from <http://localhost:8000/>:

```sh
(py2)simeon@RottenApple demo-auth>python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
127.0.0.1 - - [16/Aug/2016 16:18:34] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:34] "GET /favicon.ico HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:38] "GET /cornell_osd_gauth.html HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:38] "GET /openseadragon200/openseadragon.min.js HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:38] "GET /jquery-1.11.1.min.js HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:38] "GET /iiif-auth-100.js HTTP/1.1" 200 -
127.0.0.1 - - [16/Aug/2016 16:18:38] "GET /openseadragon200/images/zoomin_rest.png HTTP/1.1" 200 -
...
```

## OpenSeadragon versions

These demos rely upon having a copy of OpenSeadragon in this directory. They should work with OpenSeadragon 2.0 or 1.2.1, the github repository has a symlink `openseadragon200` to use OpenSeadragon 2.0.

## Issues with demo

  1. Demo client does not handle failures well
  2. Demo client does not handle lifetimes of access cookies or access tokens

