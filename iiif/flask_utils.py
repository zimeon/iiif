"""Utility functions and classes for Flask server implementation.

Based around IIIFManipulator objects for any manipulations
requested and is thus very slow.

Simeon Warner - 2014--2018
"""

from flask import Flask, request, make_response, redirect, abort, send_file, url_for, send_from_directory

import base64
import configargparse
import json
import logging
import os
import os.path
import re
from string import Template
import sys
try:  # python3
    from urllib.parse import urljoin, quote as urlquote
    from urllib.request import parse_keqv_list, parse_http_list
except ImportError:  # python2
    from urlparse import urljoin
    from urllib import quote as urlquote
    from urllib2 import parse_keqv_list, parse_http_list

from iiif.error import IIIFError
from iiif.request import IIIFRequest, IIIFRequestPathError, IIIFRequestBaseURI
from iiif.info import IIIFInfo


class Config(object):
    """Class to share configuration information in IIIFHandler instances.

    Designed to allow initialization from other Config
    objects and from argparse.Namespace objects in order to create
    independent copies of config data needed for each Flask request
    handler.
    """

    def __init__(self, *args):
        """Initialize new Config object copying all properties from args."""
        for arg in args:
            for k in list(arg.__dict__.keys()):
                self.__dict__[k] = arg.__dict__[k]


def html_page(title="Page Title", body=""):
    """Create HTML page as string."""
    html = "<html>\n<head><title>%s</title></head>\n<body>\n" % (title)
    html += "<h1>%s</h1>\n" % (title)
    html += body
    html += "</body>\n</html>\n"
    return html


def top_level_index_page(config):
    """HTML top-level index page which provides a link to each handler."""
    title = "IIIF Test Server on %s" % (config.host)
    body = "<ul>\n"
    for prefix in sorted(config.prefixes.keys()):
        body += '<li><a href="/%s">%s</a></li>\n' % (prefix, prefix)
    body += "</ul>\n"
    return html_page(title, body)


def identifiers(config):
    """Show list of identifiers for this prefix.

    Handles both the case of local file based identifiers and
    also image generators.

    Arguments:
        config - configuration object in which:
            config.klass_name - 'gen' if a generator function
            config.generator_dir - directory for generator code
            config.image_dir - directory for images

    Returns:
        ids - a list of ids
    """
    ids = []
    if (config.klass_name == 'gen'):
        for generator in os.listdir(config.generator_dir):
            if (generator == '__init__.py'):
                continue
            (gid, ext) = os.path.splitext(generator)
            if (ext == '.py' and
                    os.path.isfile(os.path.join(config.generator_dir, generator))):
                ids.append(gid)
    else:
        for image_file in os.listdir(config.image_dir):
            (iid, ext) = os.path.splitext(image_file)
            if (ext in ['.jpg', '.png', '.tif'] and
                    os.path.isfile(os.path.join(config.image_dir, image_file))):
                ids.append(iid)
    return ids


def prefix_index_page(config):
    """HTML index page for a specific prefix.

    The prefix seen by the client is obtained from config.client_prefix
    as opposed to the local server prefix in config.prefix. Also uses
    the identifiers(config) function to get identifiers available.

    Arguments:
        config - configuration object in which:
            config.client_prefix - URI path prefix seen by client
            config.host - URI host seen by client
            config.api_version - string for api_version
            config.manipulator - string manipulator type
            config.auth_type - string for auth type
            config.include_osd - whether OSD is included
    """
    title = "IIIF Image API services under %s" % (config.client_prefix)
    # details of this prefix handler
    body = '<p>\n'
    body += 'host = %s<br/>\n' % (config.host)
    body += 'api_version = %s<br/>\n' % (config.api_version)
    body += 'manipulator = %s<br/>\n' % (config.klass_name)
    body += 'auth_type = %s\n</p>\n' % (config.auth_type)
    # table of identifiers and example requests
    ids = identifiers(config)
    api_version = config.api_version
    default = 'native' if api_version < '2.0' else 'default'
    body += '<table border="1">\n<tr><th align="left">Image identifier</th>'
    body += '<th> </th><th>full</th>'
    if (config.klass_name != 'dummy'):
        body += '<th>256,256</th>'
        body += '<th>30deg</th>'
        if (config.include_osd):
            body += '<th> </th>'
    body += "</tr>\n"
    for identifier in sorted(ids):
        base = urljoin('/', config.client_prefix + '/' + identifier)
        body += '<tr><th align="left">%s</th>' % (identifier)
        info = base + "/info.json"
        body += '<td><a href="%s">%s</a></td>' % (info, 'info')
        suffix = "full/full/0/%s" % (default)
        body += '<td><a href="%s">%s</a></td>' % (base + '/' + suffix, suffix)
        if (config.klass_name != 'dummy'):
            suffix = "full/256,256/0/%s" % (default)
            body += '<td><a href="%s">%s</a></td>' % (base + '/' + suffix, suffix)
            suffix = "full/100,/30/%s" % (default)
            body += '<td><a href="%s">%s</a></td>' % (base + '/' + suffix, suffix)
            if (config.include_osd):
                body += '<td><a href="%s/osd.html">OSD</a></td>' % (base)
        body += "</tr>\n"
    body += "</table<\n"
    return html_page(title, body)


def host_port_prefix(host, port, prefix):
    """Return URI composed of scheme, server, port, and prefix."""
    uri = "http://" + host
    if (port != 80):
        uri += ':' + str(port)
    if (prefix):
        uri += '/' + prefix
    return uri


# Flask request handlers


def osd_page_handler(config=None, identifier=None, prefix=None, **args):
    """Flask handler to produce HTML response for OpenSeadragon view of identifier.

    Arguments:
        config - Config object for this IIIF handler
        identifier - identifier of image/generator
        prefix - path prefix
        **args - other aguments ignored
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    with open(os.path.join(template_dir, 'testserver_osd.html'), 'r') as f:
        template = f.read()
    d = dict(prefix=prefix,
             identifier=identifier,
             api_version=config.api_version,
             osd_version='2.0.0',
             osd_uri='/openseadragon200/openseadragon.min.js',
             osd_images_prefix='/openseadragon200/images',
             osd_height=500,
             osd_width=500,
             info_json_uri='info.json')
    return make_response(Template(template).safe_substitute(d))


class IIIFHandler(object):
    """IIIFHandler class."""

    def __init__(self, prefix, identifier, config, klass, auth):
        """Initialize IIIFHandler setting key configurations.

        Positional parameters:
        prefix -- URI prefix (without leading or trailing slashes)
        identifier -- identifier of image
        config -- instance of Config class
        klass -- IIIFManipulator sub-class to do manipulations
        auth -- IIIFAuth sub-class instance for auth or None
        """
        self.prefix = prefix
        self.identifier = identifier
        self.config = config
        self.klass = klass
        self.api_version = config.api_version
        self.auth = auth
        self.degraded = False
        self.logger = logging.getLogger('IIIFHandler')
        #
        # Create objects to process request
        self.iiif = IIIFRequest(api_version=self.api_version,
                                identifier=self.identifier)
        self.manipulator = klass(api_version=self.api_version)
        #
        # Set up auth object with locations if not already done
        if (self.auth and not self.auth.login_uri):
            self.auth.login_uri = self.server_and_prefix + '/login'
            if (self.auth.logout_handler is not None):
                self.auth.logout_uri = self.server_and_prefix + '/logout'
            self.auth.access_token_uri = self.server_and_prefix + '/token'
        #
        # Response headers
        # -- All responses should have CORS header
        self.headers = {'Access-control-allow-origin': '*'}

    @property
    def server_and_prefix(self):
        """Server and prefix from config."""
        return(host_port_prefix(self.config.host, self.config.port, self.prefix))

    @property
    def json_mime_type(self):
        """Return the MIME type for a JSON response.

        For version 2.0+ the server must return json-ld MIME type if that
        format is requested. Implement for 1.1 also.
        http://iiif.io/api/image/2.1/#information-request
        """
        mime_type = "application/json"
        if (self.api_version >= '1.1' and 'Accept' in request.headers):
            mime_type = do_conneg(request.headers['Accept'], [
                                  'application/ld+json']) or mime_type
        return mime_type

    @property
    def file(self):
        """Filename property for the source image for the current identifier."""
        file = None
        if (self.config.klass_name == 'gen'):
            for ext in ['.py']:
                file = os.path.join(
                    self.config.generator_dir, self.identifier + ext)
                if (os.path.isfile(file)):
                    return file
        else:
            for ext in ['.jpg', '.png', '.tif']:
                file = os.path.join(self.config.image_dir,
                                    self.identifier + ext)
                if (os.path.isfile(file)):
                    return file
        # failed, show list of available identifiers as error
        available = "\n ".join(identifiers(self.config))
        raise IIIFError(code=404, parameter="identifier",
                        text="Image resource '" + self.identifier + "' not found. Local resources available:" + available + "\n")

    def add_compliance_header(self):
        """Add IIIF Compliance level header to response."""
        if (self.manipulator.compliance_uri is not None):
            self.headers['Link'] = '<' + \
                self.manipulator.compliance_uri + '>;rel="profile"'

    def make_response(self, content, code=200, headers=None):
        """Wrapper around Flask.make_response which also adds any local headers."""
        if headers:
            for header in headers:
                self.headers[header] = headers[header]
        return make_response(content, code, self.headers)

    def image_information_response(self):
        """Parse image information request and create response."""
        dr = degraded_request(self.identifier)
        if (dr):
            self.logger.info("image_information: degraded %s -> %s" %
                             (self.identifier, dr))
            self.degraded = self.identifier
            self.identifier = dr
        else:
            self.logger.info("image_information: %s" % (self.identifier))
        # get size
        self.manipulator.srcfile = self.file
        self.manipulator.do_first()
        # most of info.json comes from config, a few things specific to image
        info = {'tile_height': self.config.tile_height,
                'tile_width': self.config.tile_width,
                'scale_factors': self.config.scale_factors
                }
        # calculate scale factors if not hard-coded
        if ('auto' in self.config.scale_factors):
            info['scale_factors'] = self.manipulator.scale_factors(
                self.config.tile_width, self.config.tile_height)
        i = IIIFInfo(conf=info, api_version=self.api_version)
        i.server_and_prefix = self.server_and_prefix
        i.identifier = self.iiif.identifier
        i.width = self.manipulator.width
        i.height = self.manipulator.height
        if (self.api_version >= '2.0'):
            # FIXME - should come from manipulator
            i.qualities = ["default", "color", "gray"]
        else:
            # FIXME - should come from manipulator
            i.qualities = ["native", "color", "gray"]
        i.formats = ["jpg", "png"]  # FIXME - should come from manipulator
        if (self.auth):
            self.auth.add_services(i)
        return self.make_response(i.as_json(),
                                  headers={"Content-Type": self.json_mime_type})

    def image_request_response(self, path):
        """Parse image request and create response."""
        # Parse the request in path
        if (len(path) > 1024):
            raise IIIFError(code=414,
                            text="URI Too Long: Max 1024 chars, got %d\n" % len(path))
        try:
            self.iiif.identifier = self.identifier
            self.iiif.parse_url(path)
        except IIIFRequestPathError as e:
            # Reraise as IIIFError with code=404 because we can't tell
            # whether there was an encoded slash in the identifier or
            # whether there was a bad number of path segments.
            raise IIIFError(code=404, text=e.text)
        except IIIFError as e:
            # Pass through
            raise e
        except Exception as e:
            # Something completely unexpected => 500
            raise IIIFError(code=500,
                            text="Internal Server Error: unexpected exception parsing request (" + str(e) + ")")
        dr = degraded_request(self.identifier)
        if (dr):
            self.logger.info("image_request: degraded %s -> %s" %
                             (self.identifier, dr))
            self.degraded = self.identifier
            self.identifier = dr
            self.iiif.quality = 'gray'
        else:
            # Parsed request OK, attempt to fulfill
            self.logger.info("image_request: %s" % (self.identifier))
        file = self.file
        self.manipulator.srcfile = file
        self.manipulator.do_first()
        if (self.api_version < '2.0' and
                self.iiif.format is None and
                'Accept' in request.headers):
            # In 1.0 and 1.1 conneg was specified as an alternative to format, see:
            # http://iiif.io/api/image/1.0/#format
            # http://iiif.io/api/image/1.1/#parameters-format
            formats = {'image/jpeg': 'jpg', 'image/tiff': 'tif',
                       'image/png': 'png', 'image/gif': 'gif',
                       'image/jp2': 'jps', 'application/pdf': 'pdf'}
            accept = do_conneg(request.headers['Accept'], list(formats.keys()))
            # Ignore Accept header if not recognized, should this be an error
            # instead?
            if (accept in formats):
                self.iiif.format = formats[accept]
        (outfile, mime_type) = self.manipulator.derive(file, self.iiif)
        # FIXME - find efficient way to serve file with headers
        self.add_compliance_header()
        return send_file(outfile, mimetype=mime_type)

    def error_response(self, e):
        """Make response for an IIIFError e.

        Also add compliance header.
        """
        self.add_compliance_header()
        return self.make_response(*e.image_server_response(self.api_version))


def iiif_info_handler(prefix=None, identifier=None,
                      config=None, klass=None, auth=None, **args):
    """Handler for IIIF Image Information requests."""
    if (not auth or degraded_request(identifier) or auth.info_authz()):
        # go ahead with request as made
        if (auth):
            logging.debug("Authorized for image %s" % identifier)
        i = IIIFHandler(prefix, identifier, config, klass, auth)
        try:
            return i.image_information_response()
        except IIIFError as e:
            return i.error_response(e)
    elif (auth.info_authn()):
        # authn but not authz -> 401
        abort(401)
    else:
        # redirect to degraded
        response = redirect(host_port_prefix(
            config.host, config.port, prefix) + '/' + identifier + '-deg/info.json')
        response.headers['Access-control-allow-origin'] = '*'
        return response
iiif_info_handler.provide_automatic_options = False


def iiif_image_handler(prefix=None, identifier=None,
                       path=None, config=None, klass=None, auth=None, **args):
    """Handler for IIIF Image Requests.

    Behaviour for case of a non-authn or non-authz case is to
    return 403.
    """
    if (not auth or degraded_request(identifier) or auth.image_authz()):
        # serve image
        if (auth):
            logging.debug("Authorized for image %s" % identifier)
        i = IIIFHandler(prefix, identifier, config, klass, auth)
        try:
            return i.image_request_response(path)
        except IIIFError as e:
            return i.error_response(e)
    else:
        # redirect to degraded (for not authz and for authn but not authz too)
        degraded_uri = host_port_prefix(
            config.host, config.port, prefix) + '/' + identifier + '-deg/' + path
        logging.info("Redirection to degraded: %s" % degraded_uri)
        response = redirect(degraded_uri)
        response.headers['Access-control-allow-origin'] = '*'
        return response
iiif_image_handler.provide_automatic_options = False


def degraded_request(identifier):
    """Return True (non-degraded id) if this is a degraded request, False otherwise."""
    if identifier.endswith('-deg'):
        return identifier[:-4]
    return False


def options_handler(**args):
    """Handler to respond to OPTIONS preflight CORS requests."""
    headers = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Methods': 'GET,OPTIONS',
               'Access-Control-Allow-Headers': 'Origin, Accept, Accept-Encoding, Authorization'}
    return make_response("", 200, headers)


def parse_accept_header(accept):
    """Parse an HTTP Accept header.

    Parses *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.

    Adapted from <https://djangosnippets.org/snippets/1042/>
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0).strip()
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(key=lambda x: -x[2])
    return result


def parse_authorization_header(value):
    """Parse the Authenticate header.

    Returns nothing on failure, opts hash on success with type='basic' or 'digest'
    and other params.

    <http://nullege.com/codes/search/werkzeug.http.parse_authorization_header>
    <http://stackoverflow.com/questions/1349367/parse-an-http-request-authorization-header-with-python>
    <http://bugs.python.org/file34041/0001-Add-an-authorization-header-to-the-initial-request.patch>
    """
    try:
        (auth_type, auth_info) = value.split(' ', 1)
        auth_type = auth_type.lower()
    except ValueError:
        return
    if (auth_type == 'basic'):
        try:
            decoded = base64.b64decode(auth_info).decode(
                'utf-8')  # b64decode gives bytes in python3
            (username, password) = decoded.split(':', 1)
        except (ValueError, TypeError):  # py3, py2
            return
        return {'type': 'basic', 'username': username, 'password': password}
    elif (auth_type == 'digest'):
        try:
            auth_map = parse_keqv_list(parse_http_list(auth_info))
        except ValueError:
            return
        logging.debug(auth_map)
        for key in 'username', 'realm', 'nonce', 'uri', 'response':
            if key not in auth_map:
                return
        if 'qop' in auth_map and ('nc' not in auth_map or 'cnonce' not in auth_map):
            return
        auth_map['type'] = 'digest'
        return auth_map
    else:
        # unknown auth type
        return


def do_conneg(accept, supported):
    """Parse accept header and look for preferred type in supported list.

    Arguments:
        accept - HTTP Accept header
        supported - list of MIME type supported by the server

    Returns:
        supported MIME type with highest q value in request, else None.

    FIXME - Should replace this with negotiator2
    """
    for result in parse_accept_header(accept):
        mime_type = result[0]
        if (mime_type in supported):
            return mime_type
    return None

######################################################################


def setup_auth_paths(app, auth, prefix, params):
    """Add URL rules for auth paths."""
    base = urljoin('/', prefix + '/')  # Must end in slash
    app.add_url_rule(base + 'login', prefix + 'login_handler',
                     auth.login_handler, defaults=params)
    app.add_url_rule(base + 'logout', prefix + 'logout_handler',
                     auth.logout_handler, defaults=params)
    if (auth.client_id_handler):
        app.add_url_rule(base + 'client', prefix + 'client_id_handler',
                         auth.client_id_handler, defaults=params)
    app.add_url_rule(base + 'token', prefix + 'access_token_handler',
                     auth.access_token_handler, defaults=params)
    if (auth.home_handler):
        app.add_url_rule(base + 'home', prefix + 'home_handler',
                         auth.home_handler, defaults=params)


def make_prefix(api_version, manipulator, auth_type):
    """Make prefix string based on configuration parameters."""
    prefix = "%s_%s" % (api_version, manipulator)
    if (auth_type and auth_type != 'none'):
        prefix += '_' + auth_type
    return prefix


def split_comma_argument(comma_sep_str):
    """Split a comma separated option into a list."""
    terms = []
    for term in comma_sep_str.split(','):
        if term:
            terms.append(term)
    return terms


def add_shared_configs(p, base_dir=''):
    """Add configargparser/argparse configs for shared argument.

    Arguments:
        p - configargparse.ArgParser object
        base_dir - base directory for file/path defaults.
    """
    p.add('--host', default='localhost',
          help="Service host")
    p.add('--port', '-p', type=int, default=8000,
          help="Service port")
    p.add('--app-host', default=None,
          help="Local application host for reverse proxy deployment, "
               "as opposed to service --host (must also specify --app-port)")
    p.add('--app-port', type=int, default=None,
          help="Local application port for reverse proxy deployment, "
               "as opposed to service --port (must also specify --app-host)")
    p.add('--image-dir', '-d', default=os.path.join(base_dir, 'testimages'),
          help="Image file directory")
    p.add('--generator-dir', default=os.path.join(base_dir, 'iiif/generators'),
          help="Generator directory for manipulator='gen'")
    p.add('--tile-height', type=int, default=512,
          help="Tile height")
    p.add('--tile-width', type=int, default=512,
          help="Tile width")
    p.add('--gauth-client-secret', default=os.path.join(base_dir, 'client_secret.json'),
          help="Name of file with Google auth client secret")
    p.add('--include-osd', action='store_true',
          help="Include a page with OpenSeadragon for each source")
    p.add('--access-cookie-lifetime', type=int, default=3600,
          help="Set access cookie lifetime for authenticated access in seconds")
    p.add('--access-token-lifetime', type=int, default=10,
          help="Set access token lifetime for authenticated access in seconds")
    p.add('--config', is_config_file=True, default=None,
          help='Read config from given file path')
    p.add('--debug', action='store_true',
          help="Set debug mode for web application. INSECURE!")
    p.add('--verbose', '-v', action='store_true',
          help="Be verbose")
    p.add('--quiet', '-q', action='store_true',
          help="Minimal output only")


def add_handler(app, config):
    """Add a single handler to the app.

    Adds one IIIF Image API handler to app, with config from config.

    Arguments:
        app - Flask app
        config - Configuration object in which:
            config.prefix - String path prefix for this handler
            config.client_prefix - String path prefix seen by client (which may be different
                because of reverse proxy or such
            config.klass_name - Manipulator class, e.g. 'pil'
            config.api_version - e.g. '2.1'
            config.include_osd - True or False to include OSD
            config.gauth_client_secret_file - filename if auth_type='gauth'
            config.access_cookie_lifetime - number of seconds
            config.access_token_lifetime - number of seconds
            config.auth_type - Auth type string or 'none'

    Returns True on success, nothing otherwise.
    """
    auth = None
    if (config.auth_type is None or config.auth_type == 'none'):
        pass
    elif (config.auth_type == 'gauth'):
        from iiif.auth_google import IIIFAuthGoogle
        auth = IIIFAuthGoogle(client_secret_file=config.gauth_client_secret_file)
    elif (config.auth_type == 'basic'):
        from iiif.auth_basic import IIIFAuthBasic
        auth = IIIFAuthBasic()
    elif (config.auth_type == 'clickthrough'):
        from iiif.auth_clickthrough import IIIFAuthClickthrough
        auth = IIIFAuthClickthrough()
    elif (config.auth_type == 'kiosk'):
        from iiif.auth_kiosk import IIIFAuthKiosk
        auth = IIIFAuthKiosk()
    elif (config.auth_type == 'external'):
        from iiif.auth_external import IIIFAuthExternal
        auth = IIIFAuthExternal()
    else:
        logging.error("Unknown auth type %s, ignoring" % (config.auth_type))
        return
    if (auth is not None):
        auth.access_cookie_lifetime = config.access_cookie_lifetime
        auth.access_token_lifetime = config.access_token_lifetime
    klass = None
    if (config.klass_name == 'pil'):
        from iiif.manipulator_pil import IIIFManipulatorPIL
        klass = IIIFManipulatorPIL
    elif (config.klass_name == 'netpbm'):
        from iiif.manipulator_netpbm import IIIFManipulatorNetpbm
        klass = IIIFManipulatorNetpbm
    elif (config.klass_name == 'dummy'):
        from iiif.manipulator import IIIFManipulator
        klass = IIIFManipulator
    elif (config.klass_name == 'gen'):
        from iiif.manipulator_gen import IIIFManipulatorGen
        klass = IIIFManipulatorGen
    else:
        logging.error("Unknown manipulator type %s, ignoring" % (config.klass_name))
        return
    base = urljoin('/', config.prefix + '/')  # ensure has trailing slash
    client_base = urljoin('/', config.client_prefix + '/')  # ensure has trailing slash
    logging.warning("Installing %s IIIFManipulator at %s v%s %s" %
                    (config.klass_name, base, config.api_version, config.auth_type))
    params = dict(config=config, klass=klass, auth=auth, prefix=config.client_prefix)
    app.add_url_rule(base.rstrip('/'), 'prefix_index_page',
                     prefix_index_page, defaults={'config': config})
    app.add_url_rule(base, 'prefix_index_page',
                     prefix_index_page, defaults={'config': config})
    app.add_url_rule(base + '<string(minlength=1):identifier>/info.json',
                     'options_handler', options_handler, methods=['OPTIONS'])
    app.add_url_rule(base + '<string(minlength=1):identifier>/info.json',
                     'iiif_info_handler', iiif_info_handler, methods=['GET'], defaults=params)
    if (config.include_osd):
        app.add_url_rule(base + '<string(minlength=1):identifier>/osd.html',
                         'osd_page_handler', osd_page_handler, methods=['GET'], defaults=params)
    app.add_url_rule(base + '<string(minlength=1):identifier>/<path:path>',
                     'iiif_image_handler', iiif_image_handler, methods=['GET'], defaults=params)
    if (auth):
        setup_auth_paths(app, auth, config.client_prefix, params)
    # redirects to info.json must come after auth
    app.add_url_rule(base + '<string(minlength=1):identifier>',
                     'iiif_info_handler',
                     redirect_to=client_base + '<identifier>/info.json')
    app.add_url_rule(base + '<string(minlength=1):identifier>/',
                     'iiif_info_handler',
                     redirect_to=client_base + '<identifier>/info.json')
    return True


def serve_static(filename=None, prefix='', basedir=None):
    """Handler for static files: server filename in basedir/prefix.

    If not specified then basedir defaults to the local third_party
    directory.
    """
    if not basedir:
        basedir = os.path.join(os.path.dirname(__file__), 'third_party')
    return send_from_directory(os.path.join(basedir, prefix), filename)


class ReverseProxied(object):
    """Wrap the application call to deal with a reverse proxy setup.

    Overrides HTTP_HOST environment setting.
    See: <http://flask.pocoo.org/snippets/35/>
    """

    def __init__(self, app, host):
        """Initialize reverse proxy wrapper, store host.

        Arguments:
            app - the application being reverse proxied
            host - the configured host name for the application
        """
        self.app = app
        self.host = host

    def __call__(self, environ, start_response):
        """Set environment with service host."""
        environ['HTTP_HOST'] = self.host
        return self.app(environ, start_response)


def write_pid_file():
    """Write a file with the PID of this server instance.

    Call when setting up a command line testserver.
    """
    pidfile = os.path.basename(sys.argv[0])[:-3] + '.pid'  # strip .py, add .pid
    with open(pidfile, 'w') as fh:
        fh.write("%d\n" % os.getpid())
        fh.close()


def setup_app(app, cfg):
    """Setup Flask app and handle reverse proxy setup if configured.

    Arguments:
        app - Flask application
        cfg - configuration data
    """
    # Set up app_host and app_port in case that we are running
    # under reverse proxy setup, otherwise they default to
    # config.host and config.port.
    if (cfg.app_host and cfg.app_port):
        logging.warning("Reverse proxy for service at http://%s:%d/ ..." % (cfg.host, cfg.port))
        app.wsgi_app = ReverseProxied(app.wsgi_app, cfg.host)
    elif (cfg.app_host or cfg.app_port):
        logging.critical("Must specify both app-host and app-port for reverse proxy configuration, aborting")
        sys.exit(1)
    else:
        cfg.app_host = cfg.host
        cfg.app_port = cfg.port
    logging.warning("Setup server on http://%s:%d/ ..." % (cfg.app_host, cfg.app_port))
    return(app)
