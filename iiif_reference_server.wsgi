#!/usr/bin/env python
"""
See: http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/

Apache configuration will be something like:

LoadModule wsgi_module modules/mod_wsgi.so
WSGIDaemonProcess iiifreferenceserver threads=20 maximum-requests=10000 user=apache
WSGIProcessGroup iiifreferenceserver
WSGIPassAuthorization On
WSGIScriptAlias /iiif_reference_server /FULL_PATH_TO_THIS_FILE/iiif_reference_server.wsgi

It is important that these directives are included only once in the Apache
configuration, it is not allowed to import the same WSGI configuration into
two virtual hosts (e.g. SSL and non-SSL) in the Apache configuration.
"""

# Use dev copy of IIIF modules if present in same dir as this script
import os
import sys
mydir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mydir)

# Configure and create iiif_reference_server application
#
# Note that by default iiif_reference_server.get_config(..) will look for a
# file `iiif_reference_server.cfg` in base_dir for configuration
import iiif_reference_server
cfg = iiif_reference_server.get_config(base_dir=mydir)
application = iiif_reference_server.create_reference_server_flask_app(cfg)
iiif_reference_server.setup_app(application, cfg)
