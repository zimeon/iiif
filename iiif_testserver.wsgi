#!/usr/bin/env python
"""
See: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

Have this running with Apache and the following config

#LoadModule wsgi_module modules/mod_wsgi.so
WSGIDaemonProcess iiiftestserver threads=20 maximum-requests=10000 user=apache
WSGIProcessGroup iiiftestserver
WSGIPassAuthorization On
WSGIScriptAlias /iiif_auth_test /users/sw272/src/iiif/iiif_testserver_flask.wsgi
"""

# dev copy of IIIF modules
import sys
sys.path.insert(0, '/users/sw272/src/iiif')

# load my app
from iiif_testserver_flask import app as application
