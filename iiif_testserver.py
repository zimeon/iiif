#!/usr/bin/env python
"""Crude webserver that services IIIF Image API requests

Relies upon IIIFManipulator objects to do any manipulations
requested and is thus very slow. Supports a number of different
versions of the specification via different base URIs (prefixes).

Simeon Warner - 2014...
"""

from flask import Flask, request, make_response, redirect, abort, send_file, url_for

import base64
import logging 
import re
import json
import optparse
import os
import os.path
import urllib
import urllib2

from iiif.error import IIIFError
from iiif.request import IIIFRequest,IIIFRequestBaseURI
from iiif.info import IIIFInfo

class Config(object):
    def __init__(self,*args):
        """Create new Config copying all properties from args

        Designed to allow initialization from other Config
        objects and from optparse.Values objects.
        """ 
        for arg in args:
            for k in arg.__dict__.keys():
                self.__dict__[k] = arg.__dict__[k]

def no_op(self,format,*args):
    """Function that does nothing - no-op

    Used to silence logging
    """
    pass

def html_page(title="Page Title",body=""):
    """Create HTML page as string"""
    html =  "<html>\n<head><title>%s</title></head>\n<body>\n" % (title)
    html += "<h1>%s</h1>\n" % (title)
    html += body
    html += "</body>\n</html>\n"
    return html

def top_level_index_page(config):
    """HTML top-level index page"""
    http_host = request.environ.get('HTTP_HOST','')
    title = "iiif_testserver on %s" % (http_host)
    body = "<ul>\n"
    for prefix in sorted(config.prefixes):
        body += '<li><a href="/%s">%s</a></li>\n' % (prefix,prefix)
    body += "</ul>\n"
    return html_page( title, body )

def prefix_index_page(config=None, prefix=None):
    """HTML index page for a specific prefix"""
    http_host = request.environ.get('HTTP_HOST','')
    title = "Prefix %s  (from iiif_testserver on %s)" % (prefix,http_host)
    # details of this prefix handler
    body = '<p>\n'
    body += 'api_version = %s<br/>\n' % (config.api_version)
    body += 'manipulator = %s<br/>\n' % (config.klass_name)
    body += 'auth_type = %s\n</p>\n' % (config.auth_type)
    # table of files and example requests
    files = os.listdir(config.image_dir)
    api_version = config.api_version
    default = 'native' if api_version<'2.0' else 'default'
    body += '<table border="1">\n<tr><th>Source image</th>'
    body += '<th> </th><th>full</th>'
    if (prefix!='dummy'):
        body += '<th>256,256</th>'
        body += '<th>30deg</th>'
    body += "</tr>\n"
    for file in sorted(files):
        body += "<tr><th>%s</th>" % (file)
        info = "/%s/%s/info.json" % (prefix,file)
        body += '<td><a href="%s">%s</a></td>' % (info,'info')
        suffix = "full/full/0/%s" % (default)
        url = "/%s/%s/%s" % (prefix,file,suffix)
        body += '<td><a href="%s">%s</a></td>' % (url,suffix)
        if (prefix!='dummy'):
            suffix = "full/256,256/0/%s" % (default)
            url = "/%s/%s/%s" % (prefix,file,suffix)
            body += '<td><a href="%s">%s</a></td>' % (url,suffix)
            suffix = "full/100,/30/%s" % (default)
            url = "/%s/%s/%s" % (prefix,file,suffix)
            body += '<td><a href="%s">%s</a></td>' % (url,suffix)
        body += "</tr>\n"
    body += "</table<\n"
    return html_page( title, body )

def host_port_prefix(host,port,prefix):
    """Return URI composed of scheme, server, port, and prefix"""
    uri = "http://"+host
    if (host!=80):
        uri += ':'+str(port)
    if (prefix):
        uri += '/'+prefix
    return uri

#########################################################################

class IIIFHandler(object):

    def __init__(self, prefix, identifier, config, klass, auth):
        self.prefix = prefix
        self.identifier = identifier
        self.config = config
        self.klass = klass
        self.api_version = config.api_version
        self.auth = auth
        self.degraded = False
        self.logger = logging.getLogger('IIIFHandler')
        # Create objects to process request
        self.iiif = IIIFRequest(baseurl='/'+self.prefix+'/',identifier=self.identifier,api_version=self.api_version)
        self.manipulator = klass(api_version=self.api_version)
        # Set up auth object with locations if not already done
        if (self.auth and not self.auth.login_uri):
            self.auth.login_uri = self.server_and_prefix+'/login'
            self.auth.logout_uri = self.server_and_prefix+'/logout'
            self.auth.access_token_uri = self.server_and_prefix+'/token'
        # Response headers
        # -- All responses should have CORS header
        self.headers = {'Access-control-allow-origin': '*'}

    @property
    def server_and_prefix(self):
        return(host_port_prefix(self.config.host,self.config.port,self.prefix))

    @property
    def json_mime_type(self):
        """Return the MIME type for a JSON response

        For version 2.0 the server must return json-ld MIME type if that
        format is requested. Implement for 1.1 also.
        http://iiif.io/api/image/2.0/#information-request
        """
        mime_type = "application/json"
        if (self.api_version>='1.1' and
            'Accept' in request.headers):
            mime_type = do_conneg(request.headers['Accept'],['application/ld+json']) or mime_type
        return mime_type

    @property
    def file(self):
        """Filename property for the source image for the current identifier"""
        file = None
        for ext in ['','.jpg','.png','.tif']:
            file = os.path.join(self.config.image_dir,self.identifier+ext)
            if (os.path.isfile(file)):
                return file
        # failed, show list of files as error
        images_available=""
        for image_file in os.listdir(self.config.image_dir):
            if (os.path.isfile(os.path.join(self.config.image_dir,image_file))):
                images_available += "  "+image_file+"\n"
        raise IIIFError(code=404,parameter="identifier",
                        text="Image resource '"+self.identifier+"' not found. Local image files available:\n" + images_available)

    def add_compliance_header(self):
        if (self.manipulator.compliance_uri is not None):
            self.headers['Link']='<'+self.manipulator.compliance_uri+'>;rel="profile"'   

    def make_response(self, content, code=200, content_type=None):
        """Wrapper around Flask.make_response which also added headers"""
        if (content_type):
            self.headers['Content-Type']=content_type
        return make_response(content,code,self.headers)

    def image_information_response(self):
        dr = degraded_request(self.identifier)
        if (dr):
            self.logger.info("image_information: degraded %s -> %s" % (self.identifier,dr))
            self.degraded = self.identifier
            self.identifier = dr
        else:
            self.logger.info("image_information: %s" % (self.identifier))
        # get size
        self.manipulator.srcfile=self.file
        self.manipulator.do_first()
        # most of info.json comes from config, a few things specific to image
        info = { 'tile_height': self.config.tile_height,
                 'tile_width': self.config.tile_width,
                 'scale_factors' : self.config.scale_factors
               }
        i = IIIFInfo(conf=info,api_version=self.api_version)
        i.server_and_prefix = self.server_and_prefix
        i.identifier = self.iiif.identifier
        i.width = self.manipulator.width
        i.height = self.manipulator.height
        if (self.api_version>='2.0'):
            i.qualities = [ "default", "color", "gray" ] #FIXME - should come from manipulator
        else:
            i.qualities = [ "native", "color", "gray" ] #FIXME - should come from manipulator
        i.formats = [ "jpg", "png" ] #FIXME - should come from manipulator
        if (self.auth):
            self.auth.add_services(i)
        return self.make_response(i.as_json(),content_type=self.json_mime_type)

    def image_request_response(self, path):
        # Parse the request in path
        if (len(path)>1024):
            raise IIIFError(code=414,
                            text="URI Too Long: Max 1024 chars, got %d\n" % len(path))
        #print "GET " + path
        try:
            self.iiif.identifier = self.identifier
            self.iiif.parse_url(path)
        except IIIFRequestBaseURI as e:
            info_uri = self.server_and_prefix + '/' + urllib.quote(self.iiif.identifier) + '/info.json'
            raise IIIFError(code=303, 
                            headers={'Location': info_uri})
        except IIIFError as e:
            # Pass through
            raise e
        except Exception as e:
            # Something completely unexpected => 500
            raise IIIFError(code=500,
                            text="Internal Server Error: unexpected exception parsing request (" + str(e) + ")")
        dr = degraded_request(self.identifier)
        if (dr):
            self.logger.info("image_request: degraded %s -> %s" % (self.identifier,dr))
            self.degraded = self.identifier
            self.identifier = dr
            self.iiif.quality = 'gray'
        else:
            self.logger.info("image_request: %s" % (self.identifier))        # Parsed request OK, attempt to fulfill
        file = self.file
        self.manipulator.srcfile=file
        self.manipulator.do_first()
        if (self.api_version<'2.0' and
            self.iiif.format is None and
            'Accept' in request.headers):
            # In 1.0 and 1.1 conneg was specified as an alternative to format, see:
            # http://iiif.io/api/image/1.0/#format
            # http://iiif.io/api/image/1.1/#parameters-format
            formats = { 'image/jpeg': 'jpg', 'image/tiff': 'tif',
                        'image/png': 'png', 'image/gif': 'gif',
                        'image/jp2': 'jps', 'application/pdf': 'pdf' }
            accept = do_conneg( request.headers['Accept'], formats.keys() )
            # Ignore Accept header if not recognized, should this be an error instead?
            if (accept in formats):
                self.iiif.format = formats[accept]
        (outfile,mime_type)=self.manipulator.derive(file,self.iiif)
        # FIXME - find efficient way to serve file with headers
        self.add_compliance_header()
        return send_file(open(outfile,'r'),mimetype=mime_type)

    def error_response(self, e):
        """Make response for an IIIFError e

        Looks also to see whether an extra attribute e.headers is set to
        a dict with extra header fields
        """
        for header in e.headers:
            self.headers[header]=e.headers[header]
        self.add_compliance_header()
        return make_response(str(e),e.code,{'Content-Type':e.content_type})

def iiif_info_handler(prefix=None, identifier=None, config=None, klass=None, auth=None, **args):
    """Handler for IIIF Image Information requests"""
    if (not auth or degraded_request(identifier) or auth.info_authz()):
        # go ahead with request as made
        print "Authorized for image %s" % identifier
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
        response = redirect(host_port_prefix(config.host,config.port,prefix)+'/'+identifier+'-deg/info.json')
        response.headers['Access-control-allow-origin']='*'
        return response 
iiif_info_handler.provide_automatic_options = False

def iiif_image_handler(prefix=None, identifier=None, path=None, config=None, klass=None, auth=None, **args):
    """Handler for IIIF Image Requests

    Behaviour for case of a non-authn or non-authz case is to 
    return 403.
    """
    if (not auth or degraded_request(identifier) or auth.image_authz()):
        # serve image
        print "Authorized for image %s" % identifier
        i = IIIFHandler(prefix, identifier, config, klass, auth)
        try:
            return i.image_request_response(path)
        except IIIFError as e:
            return i.error_response(e)
    else:
        # redirect to degraded (for not authz and for authn but not authz too)
        degraded_uri = host_port_prefix(config.host,config.port,prefix)+'/'+identifier+'-deg/'+path
        print "Redirection to degraded: %s" % degraded_uri
        response = redirect(degraded_uri)
        response.headers['Access-control-allow-origin']='*'
        return response
iiif_image_handler.provide_automatic_options = False

def degraded_request(identifier):
    """Returns True (non-degraded id) if this is a degraded request, False otherwise"""
    if identifier.endswith('-deg'):
       return identifier[:-4]
    return False

def options_handler(**args):
    """Handler to respond to OPTIONS requests"""
    headers = { 'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Origin, Accept, Authorization' }
    return make_response("", 200, headers)

def parse_accept_header(accept):
    """Parse the Accept header *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.
    
    Taken from <https://djangosnippets.org/snippets/1042/>
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(lambda x, y: -cmp(x[2], y[2]))
    return result

def parse_authorization_header(value):
    """Parse the Authenticate header

    Returns nothing on failure, opts hash on success with type='basic' or 'digest'
    and other params.

    <http://nullege.com/codes/search/werkzeug.http.parse_authorization_header>
    <http://stackoverflow.com/questions/1349367/parse-an-http-request-authorization-header-with-python>
    <http://bugs.python.org/file34041/0001-Add-an-authorization-header-to-the-initial-request.patch>
    """
    try:
        (auth_type, auth_info) = value.split(' ', 1)
        auth_type = auth_type.lower()
    except ValueError as e:
        return
    if (auth_type == 'basic'):
        try:
            (username, password) = base64.b64decode(auth_info).split(':', 1)
        except Exception as e:
            return
        return {'type':'basic', 'username': username, 'password': password}
    elif (auth_type == 'digest'):
        auth_map = urllib2.parse_keqv_list(urllib2.parse_http_list(auth_info))
        print auth_map
        for key in 'username', 'realm', 'nonce', 'uri', 'response':
            if not key in auth_map:
                return
            if 'qop' in auth_map:
                if not auth_map.get('nc') or not auth_map.get('cnonce'):
                    return
        auth_map['type']='digest'
        return auth_map
    else:
        # unknown auth type
        return

def do_conneg(accept,supported):
    """Parse accept header and look for preferred type in supported list

    accept parameter is HTTP header, supported is a list of MIME types
    supported by the server. Returns the supported MIME type with highest
    q value in request, else None.
    """
    for result in parse_accept_header(accept):
        mime_type=result[0]
        if (mime_type in supported):
            return(mime_type)
    return(None)

######################################################################

def setup_auth_paths(app, auth, prefix, params):
    """Add URL rules for auth paths
    """
    base = '/'+prefix+'/'
    app.add_url_rule(base+'login', prefix+'login_handler', auth.login_handler, defaults=params)
    app.add_url_rule(base+'logout', prefix+'logout_handler', auth.logout_handler, defaults=params)
    if (auth.client_id_handler):
        app.add_url_rule(base+'client', prefix+'client_id_handler', auth.client_id_handler, defaults=params)
    app.add_url_rule(base+'token', prefix+'access_token_handler', auth.access_token_handler, defaults=params)
    if (auth.home_handler):
        app.add_url_rule(base+'home', prefix+'home_handler', auth.home_handler, defaults=params)

def make_prefix(api_version,manipulator,auth_type):
    """Make prefix string based on configuration parameters"""
    prefix = "%s_%s" % (api_version,manipulator)
    if (auth_type and auth_type!='none'):
        prefix += '_'+auth_type
    return(prefix)

def split_option(comma_sep_str):
    return  comma_sep_str.split(',') #FIXME - make more flexible

def setup_options():
    # Options and arguments
    p = optparse.OptionParser(description='IIIF Image Testserver')
    p.add_option('--host', default='localhost',
                 help="Server host (default %default)")
    p.add_option('--port', '-p', type='int', default=8000,
                 help="Server port (default %default)")
    p.add_option('--image-dir','-d', default='testimages',
                 help="Image directory (default %default)")
    p.add_option('--tile-height', type='int', default=256,
                 help="Tile height (default %default)")
    p.add_option('--tile-width', type='int', default=256,
                 help="Tile width (default %default)")
    p.add_option('--scale-factors', default='1,2,4,8',
                 help="Set of tile scale factors (default %default)")
    p.add_option('--api-versions', default='1.0,1.1,2.0',
                 help="Set of API versions to support (default %default)")
    p.add_option('--manipulators',default='pil',
                 help="Set of manipuators to instantiate (from dummy,netpbm,pil; default %default")
    p.add_option('--auth-types',default='none',
                 help="Set of authentication types to support (default %default)")
    p.add_option('--gauth-client-secret', default='client_secret.json',
                 help="Name of file with Google auth client secret (default %default)")
    p.add_option('--pages-dir', default='testpages',
                 help="Test pages directory (default %default)")
    p.add_option('--draft', action='store_true',
                 help="Enable features implementing draft IIIF specifications: v2.1 and auth")
    p.add_option('--debug', action='store_true',
                 help="Set debug mode for web application. INSECURE!")
    p.add_option('--verbose', '-v', action='store_true',
                 help="Be verbose")
    p.add_option('--quiet','-q', action='store_true',
                 help="Minimal output only")
    (opt, args) = p.parse_args()

    if (opt.debug):
        opt.verbose = True
    elif (opt.verbose):
        opt.quiet = False

    # Split list arguments
    opt.scale_factors = split_option(opt.scale_factors)
    opt.manipulators = split_option(opt.manipulators)
    opt.api_versions = split_option(opt.api_versions)
    opt.auth_types = split_option(opt.auth_types)

    # Draft features...
    if (opt.draft and '2.1' not in opt.api_versions):
        opt.api_versions.append('2.1')
    if (opt.draft and 'gauth' not in opt.auth_types):
        opt.auth_types.append('gauth') 
    if (opt.draft and 'basic' not in opt.auth_types):
        opt.auth_types.append('basic') 

    return(opt)

def add_handler(app, config, prefixes):
    """Add a single handler to the app

    Adds handlers to app, with config from config. Add prefix to list
    in prefixes.
    """
    wsgi_prefix = make_prefix(config.api_version,config.klass_name,config.auth_type)
    prefix = wsgi_prefix
    if (config.container_prefix):
        prefix = os.path.join(config.container_prefix, wsgi_prefix) 
    prefixes.append(prefix)
    auth = None
    if (config.auth_type is None or config.auth_type=='none'):
        pass
    elif (config.auth_type=='gauth'):
        from iiif.auth_google import IIIFAuthGoogle
        auth = IIIFAuthGoogle(client_secret_file=config.gauth_client_secret_file)
    elif (config.auth_type=='basic'):
        from iiif.auth_basic import IIIFAuthBasic
        auth = IIIFAuthBasic()
    else:
        print "Unknown auth type %s, ignoring" % (config.auth_type)
        return
    klass=None
    if (config.klass_name=='pil'):
        from iiif.manipulator_pil import IIIFManipulatorPIL
        klass=IIIFManipulatorPIL
    elif (config.klass_name=='netpbm'):
        from iiif.manipulator_netpbm import IIIFManipulatorNetpbm
        klass=IIIFManipulatorNetpbm
    elif (config.klass_name=='dummy'):
        from iiif.manipulator import IIIFManipulator
        klass=IIIFManipulator
    else:
        print "Unknown manipulator type %s, ignoring" % (config.klass_name)
        return
    print "Installing %s IIIFManipulator at /%s/ v%s %s" % (config.klass_name,prefix,config.api_version,config.auth_type)
    params=dict(config=config, klass=klass, auth=auth, prefix=prefix)
    app.add_url_rule('/'+wsgi_prefix, 'prefix_index_page', prefix_index_page, defaults={'config':config,'prefix':prefix})
    app.add_url_rule('/'+wsgi_prefix+'/<string(minlength=1):identifier>/info.json', 'options_handler', options_handler, methods=['OPTIONS'])
    app.add_url_rule('/'+wsgi_prefix+'/<string(minlength=1):identifier>/info.json', 'iiif_info_handler', iiif_info_handler, methods=['GET'], defaults=params)
    app.add_url_rule('/'+wsgi_prefix+'/<string(minlength=1):identifier>/<path:path>', 'iiif_image_handler', iiif_image_handler, methods=['GET'], defaults=params)
    if (auth):
        setup_auth_paths(app, auth, wsgi_prefix, params)
    # redirects to info.json must come after auth
    app.add_url_rule('/'+wsgi_prefix+'/<string(minlength=1):identifier>', 'iiif_info_handler', redirect_to='/'+prefix+'/<identifier>/info.json')
    app.add_url_rule('/'+wsgi_prefix+'/<string(minlength=1):identifier>/', 'iiif_info_handler', redirect_to='/'+prefix+'/<identifier>/info.json')

def create_app(opt):
    """Create Flask application with one or more IIIF handlers"""
    logging_level = logging.WARNING
    if (opt.verbose):
        logging_level = logging.INFO
    elif (opt.quiet):
        logging_level = logging.ERROR
    logging.basicConfig( format='%(name)s: %(message)s', level=logging_level )

    # Create Flask app
    app = Flask(__name__, static_url_path='/'+opt.pages_dir)
    Flask.secret_key="SECRET_HERE"
    app.debug = opt.debug

    # Create shared configuration dict based on options
    config = Config(opt)
    config.homedir=os.path.dirname(os.path.realpath(__file__))
    config.gauth_client_secret_file=os.path.join(config.homedir,config.gauth_client_secret)

    prefixes = []
    for api_version in opt.api_versions:
        for klass_name in opt.manipulators:
            for auth_type in opt.auth_types:
                # auth only for >=2.1
                if (auth_type!='none' and float(api_version)<2.1):
                    continue
                handler_config = Config(config)
                handler_config.api_version = api_version
                handler_config.klass_name = klass_name
                handler_config.auth_type = auth_type
                add_handler(app,handler_config,prefixes)

    # Index page
    config.prefixes = prefixes
    app.add_url_rule('/', 'top_level_index_page', top_level_index_page, defaults={'config':config})

    return(app)


if __name__ == '__main__':
    # Command line, run own server
    pidfile=os.path.basename(__file__)[:-3]+'.pid' #strip .py, add .pid
    with open(pidfile,'w') as fh:
        fh.write("%d\n" % os.getpid())
        fh.close()
    opt = setup_options()
    opt.container_prefix = ''
    app = create_app(opt)
    print "Starting test server on http://%s:%d/ ..." % (opt.host,opt.port)
    app.run(host=opt.host, port=opt.port)
else:
    opt = optparse.Values()
    opt.verbose = 1
    opt.debug = 1
    opt.draft = 1
    mydir=os.path.dirname(os.path.realpath(__file__))
    opt.pages_dir = mydir+'/testpages'
    opt.image_dir = mydir+'/testimages'
    opt.tile_width = 512
    opt.tile_height = 512
    opt.scale_factors = [1,2,4,8]
    opt.api_versions = ['1.0','1.1','2.0','2.1']
    opt.auth_types = ['none','gauth','basic']
    opt.manipulators = ['dummy','netpbm','pil']
    opt.container_prefix = 'iiif_auth_test'
    # Should get the following from WSGI environ, 
    # see https://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines
    opt.host = 'resync.library.cornell.edu' #FIXME - get from WSGI
    opt.port = 80
    opt.gauth_client_secret = 'client_secret.json'
    app = create_app(opt)
