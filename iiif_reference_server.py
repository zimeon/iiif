#!/usr/bin/env python
"""Webserver that implements IIIF Image API Reference Service.

Relies upon IIIFManipulator objects to do any manipulations
requested and is thus slow/inefficient.

Simeon Warner - 2014--2018
"""

from flask import Flask
import logging
import re
import configargparse
import os
import os.path
import sys

from iiif.flask_utils import Config, write_pid_file, add_handler, make_prefix, ReverseProxied, setup_app, split_comma_argument, add_shared_configs


def get_config(base_dir=''):
    """Get config from defaults, config file and/or parse arguments.

    Uses configargparse to allow argments to be set from a config file
    or via command line arguments.

      base_dir - set a specific base directory for file/path defaults.
    """
    p = configargparse.ArgParser(description='IIIF Image API Reference Service',
                                 default_config_files=[os.path.join(base_dir, 'iiif_reference_server.cfg')],
                                 formatter_class=configargparse.ArgumentDefaultsHelpFormatter)
    add_shared_configs(p, base_dir)
    p.add('--scale-factors', default='auto',
          help="Set of tile scale factors or 'auto' to calculate for each image "
               "such that there are tiles up to the full image")
    p.add('--api-versions', default='1.0,1.1,2.0,2.1,3.0',
          help="Set of API versions to support")
    args = p.parse_args()

    if (args.debug):
        args.verbose = True
    elif (args.verbose):
        args.quiet = False

    # Split list arguments
    args.scale_factors = split_comma_argument(args.scale_factors)
    args.api_versions = split_comma_argument(args.api_versions)

    logging_level = logging.WARNING
    if args.verbose:
        logging_level = logging.INFO
    elif args.quiet:
        logging_level = logging.ERROR
    logging.basicConfig(format='%(name)s: %(message)s', level=logging_level)

    return(args)


def create_reference_server_flask_app(cfg):
    """Create referece server Flask application with one or more IIIF handlers."""
    # Create Flask app
    app = Flask(__name__)
    Flask.secret_key = "SECRET_HERE"
    app.debug = cfg.debug
    # Install request handlers
    client_prefixes = dict()
    for api_version in cfg.api_versions:
        handler_config = Config(cfg)
        handler_config.api_version = api_version
        handler_config.klass_name = 'pil'
        handler_config.auth_type = 'none'
        # Set same prefix on local server as expected on iiif.io
        handler_config.prefix = "api/image/%s/example/reference" % (api_version)
        handler_config.client_prefix = handler_config.prefix
        add_handler(app, handler_config)
    return app


if __name__ == '__main__':
    # Command line, run server
    write_pid_file()
    cfg = get_config()
    app = create_reference_server_flask_app(cfg)
    setup_app(app, cfg)
    app.run(host=cfg.app_host, port=cfg.app_port)
