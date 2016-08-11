#!/usr/bin/env python
"""
See: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

Apache configuration will be something like:

LoadModule wsgi_module modules/mod_wsgi.so
WSGIDaemonProcess iiiftestserver threads=20 maximum-requests=10000 user=apache
WSGIProcessGroup iiiftestserver
WSGIPassAuthorization On
WSGIScriptAlias /iiif_auth_test /FULL_PATH_TO_THIS_FILE/iiif_testserver.wsgi

It is important that these directives are included only once in the Apache
configuration, it is not allowed to import the same WSGI configuration into
two virtual hosts (e.g. SSL and non-SSL) in the Apache configuration.
"""

# use dev copy of IIIF modules if present in same dir as this script
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# load my app
from iiif_testserver import app as application
