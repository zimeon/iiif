#!/usr/bin/env python
"""Crude webserver that services IIIF Image API requests.

Relies upon IIIFManipulator objects to do any manipulations
requested and is thus very slow. Supports a number of different
versions of the specification via different base URIs (prefixes).

Simeon Warner - 2014--2018
"""

from flask import Flask
import logging
import re
import configargparse
import os
import os.path
import sys

from iiif.flask_utils import Config, write_pid_file, add_handler, make_prefix, top_level_index_page, serve_static, ReverseProxied, setup_app, split_comma_argument, add_shared_configs


def get_config(base_dir=''):
    """Get config from defaults, config file and/or parse arguments.

    Uses configargparse to allow argments to be set from a config file
    or via command line arguments.

      base_dir - set a specific base directory for file/path defaults.
    """
    p = configargparse.ArgParser(description='IIIF Image Testserver',
                                 default_config_files=[os.path.join(base_dir, 'iiif_testserver.cfg')],
                                 formatter_class=configargparse.ArgumentDefaultsHelpFormatter)
    add_shared_configs(p, base_dir)
    p.add('--container-prefix', default='',
          help="Container prefix seen by client to add to links generated")
    p.add('--scale-factors', default='auto',
          help="Set of tile scale factors or 'auto' to calculate for each image "
               "such that there are tiles up to the full image")
    p.add('--api-versions', default='1.0,1.1,2.0,2.1',
          help="Set of API versions to support")
    p.add('--manipulators', default='pil',
          help="Set of manipuators to instantiate. May be dummy,netpbm,pil "
               "or gen for generated image")
    p.add('--auth-types', default='none',
          help="Set of authentication types to support")
    p.add('--pages-dir', default=os.path.join(base_dir, 'testpages'),
          help="Test pages directory")
    p.add('--auth', action='store_true',
          help="Enable features implementing the IIIF Authentication specification")
    args = p.parse_args()

    if (args.debug):
        args.verbose = True
    elif (args.verbose):
        args.quiet = False

    # Split list arguments
    args.scale_factors = split_comma_argument(args.scale_factors)
    args.manipulators = split_comma_argument(args.manipulators)
    args.api_versions = split_comma_argument(args.api_versions)
    args.auth_types = split_comma_argument(args.auth_types)

    # Authentication features...
    if (args.auth and 'gauth' not in args.auth_types):
        args.auth_types.append('gauth')
    if (args.auth and 'basic' not in args.auth_types):
        args.auth_types.append('basic')
    if (args.auth and 'clickthrough' not in args.auth_types):
        args.auth_types.append('clickthrough')
    if (args.auth and 'kiosk' not in args.auth_types):
        args.auth_types.append('kiosk')
    if (args.auth and 'external' not in args.auth_types):
        args.auth_types.append('external')

    logging_level = logging.WARNING
    if args.verbose:
        logging_level = logging.INFO
    elif args.quiet:
        logging_level = logging.ERROR
    logging.basicConfig(format='%(name)s: %(message)s', level=logging_level)

    return(args)


def create_testserver_flask_app(cfg):
    """Create testserver Flask application with one or more IIIF handlers."""
    # Create Flask app
    app = Flask(__name__, static_url_path='/' + cfg.pages_dir)
    Flask.secret_key = "SECRET_HERE"
    app.debug = cfg.debug

    # Create shared configuration dict based on options
    config = Config(cfg)
    config.homedir = os.path.dirname(os.path.realpath(__file__))
    config.gauth_client_secret_file = os.path.join(
        config.homedir, config.gauth_client_secret)

    # Install request handlers
    client_prefixes = dict()
    for api_version in cfg.api_versions:
        for klass_name in cfg.manipulators:
            for auth_type in cfg.auth_types:
                # auth only for >=2.1
                if (auth_type != 'none' and float(api_version) < 2.1):
                    continue
                handler_config = Config(config)
                handler_config.api_version = api_version
                handler_config.klass_name = klass_name
                handler_config.auth_type = auth_type
                prefix = make_prefix(api_version, klass_name, auth_type)
                client_prefix = os.path.join(config.container_prefix, prefix)
                logging.debug("prefix = %s, client_prefix = %s" % (prefix, client_prefix))
                client_prefixes[client_prefix] = prefix
                handler_config.prefix = prefix
                handler_config.client_prefix = client_prefix
                add_handler(app, handler_config)

    # Index page
    config.prefixes = client_prefixes
    app.add_url_rule('/', 'top_level_index_page',
                     top_level_index_page, defaults={'config': config})

    if cfg.include_osd:
        # OpenSeadragon files
        app.add_url_rule('/openseadragon200/<path:filename>', 'OSD pages', serve_static,
                         defaults={'prefix': 'openseadragon200'})

    return(app)


if __name__ == '__main__':
    # Command line, run server
    write_pid_file()
    cfg = get_config()
    app = setup_app(create_testserver_flask_app(cfg), cfg)
    app.run(host=cfg.app_host, port=cfg.app_port)
