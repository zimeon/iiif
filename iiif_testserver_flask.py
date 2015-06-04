#!/usr/bin/env python
"""Crude webserver that services IIIF Image API requests

Relies upon IIIFManipulator objects to do any manipulations
requested.
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
from iiif.auth import IIIFAuth

class SharedConfig(object):
    pass

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
    title = "iiif_testserver on %s:%s" % (config.host,config.port)
    body = "<ul>\n"
    for prefix in sorted(config.prefixes.keys()):
        body += '<li><a href="%s">%s</a></li>\n' % (prefix,prefix)
    body += "</ul>\n"
    return html_page( title, body )

def prefix_index_page(config=None, prefix=None):
    """HTML index page for a specific prefix"""
    title = "Prefix %s  (from iiif_testserver on %s:%s)" % (prefix,config.host,config.port)
    files = os.listdir(config.image_dir)
    api_version = config.prefixes[prefix]['api_version']
    default = 'default' if api_version>='2.0' else 'native'
    body = "<table>\n<tr><th></th>"
    body += '<th colspan="2">%s</th>' % (prefix)
    if (prefix!='dummy'):
        body += "<th>%s 256x256</th>" % (prefix)
    body += "</tr>\n"
    for file in sorted(files):
        body += "<tr><th>%s</th>" % (file)
        url = "/%s/%s/full/full/0/%s" % (prefix,file,default)
        body += '<td><a href="%s">%s</a></td>' % (url,url)
        info = "/%s/%s/info.json" % (prefix,file)
        body += '<td><a href="%s">%s</a></td>' % (info,info)
        if (prefix!='dummy'):
            url = "/%s/%s/full/256,256/0/%s" % (prefix,file,default)
            body += '<td><a href="%s">%s</a></td>' % (url,url)
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

    def __init__(self, prefix, identifier, config, klass, api_version, auth):
        self.prefix = prefix
        self.identifier = identifier
        self.config = config
        self.klass = klass
        self.api_version = api_version
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
        i = IIIFInfo(conf=self.config.info,api_version=self.api_version)
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
            accept = do_conneg( self.headers['Accept'], formats.keys() )
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

def iiif_info_handler(prefix=None, identifier=None, config=None, klass=None, api_version='2.0', auth=None):
    """Handler for IIIF Image Information requests"""
    if (not auth or degraded_request(identifier) or is_authz()):
        # go ahead with request as made
        i = IIIFHandler(prefix, identifier, config, klass, api_version, auth)
        try:
            return i.image_information_response()
        except IIIFError as e:
            return i.error_response(e)
    elif (is_authn()):
        # authn but not authz -> 401
        abort(401)
    else:
        # redirect to degraded
        response = redirect(host_port_prefix(config.host,config.port,prefix)+'/'+identifier+'-deg/info.json')
        response.headers['Access-control-allow-origin']='*'
        return response 
iiif_info_handler.provide_automatic_options = False

def iiif_image_handler(prefix=None, identifier=None, path=None, config=None, klass=None, api_version='2.0', auth=None):
    i = IIIFHandler(prefix, identifier, config, klass, api_version, auth)
    try:
        return i.image_request_response(path)
    except IIIFError as e:
        return i.error_response(e)

def degraded_request(identifier):
    """Returns True (non-degraded id) if this is a degraded request, False otherwise"""
    if identifier.endswith('-deg'):
       return identifier[:-4]
    return False

def is_authn():
    """Check to see if user if authenticated"""
    return request.cookies.get("loggedin",default='')

def is_authz(): 
    """Check to see if user if authenticated and authorized"""
    return (is_authn() and request.headers.get('Authorization', '') != '')

def iiif_login_handler(config=None, prefix=None, **args):
    """OAuth starts here. This will redirect User to Google"""
    params = {
        'response_type': 'code',
        'client_id': config.google_api_client_id,
        'redirect_uri': host_port_prefix(config.host,config.port,prefix)+'/home',
        'scope': config.google_api_scope,
        'state': request.args.get('next',default=''),
    }
    url = config.google_oauth2_url + 'auth?' + urllib.urlencode(params)
    response = redirect(url)
    response.headers['Access-control-allow-origin']='*'
    return response 

def iiif_logout_handler(**args):
    return "LOGOUT not implemented"

def iiif_client_id_handler(**args):
    return "CLIENT ID not implemented"

def iiif_access_token_handler(**args):
    # This is the next step -- client requests a token to send to info.json
    # We're going to just copy it from our cookie.
    # JSONP request to get the token to send to info.json in Auth'z header
    callback_function = request.args.get('callback',default='')
    authcode = request.args.get('code',default='')
    account = request.cookies.get('account',default='')
    if (account):
        data = {"access_token":account, "token_type": "Bearer", "expires_in": 3600}
    else:
        data = {"error":"client_unauthorized","error_description": "No login details received"}
    data_str = json.dumps(data)

    ct = "application/json"
    if (callback_function):
        data_str = "%s(%s);" % (callback_function, data_str)
        ct = "application/javascript"
    # Build response
    response = make_response(data_str,200,{'Content-Type':ct})
    if (account):
        # Set the cookie for the image content -- FIXME - need something real
        response.set_cookie('loggedin', account)
    response.set_cookie('account', expires=0)
    return response

def iiif_home_handler(config=None, prefix=None, **args):
    """Handler for /home redirect path after Goole auth

    OAuth ends up back here from Google. Set the account cookie 
    and close window to trigger next step
    """
    gresponse = google_get_token(config, prefix)
    gdata = google_get_data(config, gresponse)

    email = gdata.get('email', 'NO_EMAIL')
    name = gdata.get('name', 'NO_NAME')
    response = make_response("<html><script>window.close();</script></html>", 200, {'Content-Type':"text/html"});
    response.set_cookie("account", name+' '+email)
    return response

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

# FIXME - code to get data from Google API, should be elsewhere

def google_get_token(config, prefix):
    # Google OAuth2 helpers
    params = {
        'code': request.args.get('code',default=''),
        'client_id': config.google_api_client_id,
        'client_secret': config.google_api_client_secret,
        'redirect_uri': host_port_prefix(config.host,config.port,prefix)+'/home',
        'grant_type': 'authorization_code',
    }
    payload = urllib.urlencode(params)
    url = config.google_oauth2_url + 'token'
    req = urllib2.Request(url, payload) 
    return json.loads(urllib2.urlopen(req).read())

def google_get_data(config, response):
    """Make request to Google API to get profile data for the user"""
    params = {
        'access_token': response['access_token'],
    }
    payload = urllib.urlencode(params)
    url = config.google_api_url + 'userinfo?' + payload
    req = urllib2.Request(url)  # must be GET
    return json.loads(urllib2.urlopen(req).read())

######################################################################

def setup_auth_paths(app, base_pattern, params):
    """Add URL rules for auth paths
    """
    app.add_url_rule(base_pattern+'login', 'iiif_login_handler', iiif_login_handler, defaults=params)
    app.add_url_rule(base_pattern+'logout', 'iiif_logout_handler', iiif_login_handler, defaults=params)
    app.add_url_rule(base_pattern+'client', 'iiif_client_id_handler', iiif_client_id_handler, defaults=params)
    app.add_url_rule(base_pattern+'token', 'iiif_access_token_handler', iiif_access_token_handler, defaults=params)
    app.add_url_rule(base_pattern+'home', 'iiif_home_handler', iiif_home_handler, defaults=params)

def setup():
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
    p.add_option('--pages-dir', default='testpages',
                 help="Test pages directory (default %default)")
    p.add_option('--user-pass', default='user:pass',
                 help="Username colon password need for authentication (default %default)")
    p.add_option('--verbose', '-v', action='store_true',
                 help="Be verbose")
    p.add_option('--debug', action='store_true',
                 help="Set debug mode for web application. DEVELOPMENT ONLY")
    p.add_option('--quiet','-q', action='store_true',
                 help="Minimal output only")
    (opt, args) = p.parse_args()

    if (opt.debug):
        opt.verbose = True
    logging.basicConfig( format='%(name)s: %(message)s',
                         level=( logging.INFO if (opt.verbose) else logging.WARNING ) )

    if (opt.quiet):
        # Add no_op function as logger to silence
        IIIFRequestHandler.log_message=no_op

    # Create Flask app
    app = Flask(__name__, static_url_path='/'+opt.pages_dir)
    Flask.secret_key="SECRET_HERE"
    app.debug = opt.debug

    # Create shared configuration dict
    config = SharedConfig()
    config.host = opt.host
    config.port = opt.port
    config.image_dir = opt.image_dir
    config.user_pass = opt.user_pass
    config.info={'tile_height': opt.tile_height,
          'tile_width': opt.tile_width,
          'scale_factors' : [1,2,4,8],
    }
    for option in config.info:
        print "got %s = %s" % (option,config.info[option])
    config.prefixes = {}
    # Google auth config
    config.homedir=os.path.dirname(os.path.realpath(__file__))
    gcd=json.loads(open(os.path.join(config.homedir,'client_secret.json')).read())
    config.google_api_client_id = gcd['web']['client_id']
    config.google_api_client_secret = gcd['web']['client_secret']
    config.google_api_scope = 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
    config.google_oauth2_url = 'https://accounts.google.com/o/oauth2/'
    config.google_api_url = 'https://www.googleapis.com/oauth2/v1/'

    # Index page
    app.add_url_rule('/', 'top_level_index_page', top_level_index_page, defaults={'config':config})

    # Add handlers for all the IIIF handlers we want to support
    versions = ['1.0', '1.1', '2.0', '2.1']
    klass_names = ['pil','netpbm','dummy']
    auth_types = ['none','gauth']
    for api_version in versions:
        for klass_name in klass_names:
            for auth_type in auth_types:
                # auth only for 2.0
                if (auth_type != 'none' and api_version != '2.0'):
                    continue
                prefix = "%s_%s" % (api_version,klass_name)
                auth = None
                if (auth_type != 'none'):
                    prefix += '_'+auth_type
                    auth = IIIFAuth()
                klass=None
                if (klass_name=='pil'):
                    from iiif.manipulator_pil import IIIFManipulatorPIL
                    klass=IIIFManipulatorPIL
                elif (klass_name=='netpbm'):
                    from iiif.manipulator_netpbm import IIIFManipulatorNetpbm
                    klass=IIIFManipulatorNetpbm
                elif (klass_name=='dummy'):
                    from iiif.manipulator import IIIFManipulator
                    klass=IIIFManipulator
                else:
                    print "Unknown manipulator type %s, ignoring" % (klass_name)
                    continue
                print "Installing %s IIIFManipulator at /%s/ v%s %s" % (klass_name,prefix,api_version,auth_type)
                params=dict(config=config, klass=klass, api_version=api_version, auth=auth, prefix=prefix)
                config.prefixes[prefix]=params
                app.add_url_rule('/'+prefix, 'prefix_index_page', prefix_index_page, defaults={'config':config,'prefix':prefix})
                app.add_url_rule('/'+prefix+'/<string(minlength=1):identifier>/info.json', 'options_handler', options_handler, methods=['OPTIONS'])
                app.add_url_rule('/'+prefix+'/<string(minlength=1):identifier>/info.json', 'iiif_info_handler', iiif_info_handler, methods=['GET'], defaults=params)
                app.add_url_rule('/'+prefix+'/<string(minlength=1):identifier>/<path:path>', 'iiif_image_handler', iiif_image_handler, defaults=params)
                if (auth):
                    setup_auth_paths(app, '/'+prefix+'/', params)
                # redirects to info.json must come after auth
                app.add_url_rule('/'+prefix+'/<string(minlength=1):identifier>', 'iiif_info_handler', redirect_to='/'+prefix+'/<identifier>/info.json')
                app.add_url_rule('/'+prefix+'/<string(minlength=1):identifier>/', 'iiif_info_handler', redirect_to='/'+prefix+'/<identifier>/info.json')

    pidfile=os.path.basename(__file__)[:-3]+'.pid' #strip .py, add .pid
    with open(pidfile,'w') as fh:
        fh.write("%d\n" % os.getpid())
        fh.close()

    app.run(host=opt.host, port=opt.port)



if __name__ == '__main__':
    setup()


