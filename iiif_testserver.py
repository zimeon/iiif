#!/usr/bin/env python
"""Crude webserver that services IIIF Image API requests

Relies upon IIIFManipulator objects to do any manipulations
requested.
"""

import BaseHTTPServer
import re
import optparse
import os
import os.path
import sys
import urllib

from iiif.error import IIIFError
from iiif.request import IIIFRequest,IIIFRequestBaseURI
from iiif.info import IIIFInfo

def no_op(self,format,*args):
    """Function that does nothing - no-op

    Used to silence logging
    """
    pass

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

class IIIFRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):

    # Class data
    HOST=None
    PORT=None
    IMAGE_DIR=None
    INFO=None
    MANIPULATORS={}
    
    @classmethod
    def add_manipulator(cls, prefix, klass, api_version='2.0', auth_type=None):
        cls.MANIPULATORS[prefix]={'klass': klass, 
                                  'api_version': api_version,
                                  'auth_type': auth_type}

    def __init__(self, request, client_address, server):
        # Add some local attributes for this subclass (seems we have to 
        # do this ahead of calling the base class __init__ because that
        # does not return
        self.debug=True
        self.compliance_level=None
        self.manipulator=None
        # Cannot use super() because BaseHTTPServer.BaseHTTPRequestHandler 
        # is not new style class
        #super(IIIFRequestHandler, self).__init__(request, client_address, server)
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    @property
    def server_and_prefix(self):
        """Return URI composed of scheme, server, port, and prefix"""
        uri = "http://"+self.HOST
        if (self.PORT!=80):
            uri += ':'+str(self.PORT)
        if (self.prefix):
            uri += '/'+self.prefix
        return uri

    @property
    def json_mime_type(self):
        """Return the MIME type for a JSON response

        For version 2.0 the server must return json-ld MIME type if that
        format is requested. Implement for 1.1 also.
        http://iiif.io/api/image/2.0/#information-request
        """
        mime_type = "application/json"
        if (self.api_version>='1.1' and
            'Accept' in self.headers):
            mime_type = do_conneg(self.headers['Accept'],['application/ld+json']) or mime_type
        return mime_type

    def send_404_response(self, content='Resource Not Found'):
        """Send a plain 404 for URLs not under a known IIIF endpoint prefix"""
        self.send_response(404)
        self.send_header('Content-Type','text/plain')
        self.end_headers()
        self.wfile.write(content)
    
    def send_html_page(self,title="Page Title",body=""):
        """Send an HTML page as response"""
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self.end_headers()
        self.wfile.write("<html>\n<head><title>%s</title></head>\n<body>\n" % (title))
        self.wfile.write("<h1>%s</h1>\n" % (title))
        self.wfile.write( body )
        self.wfile.write("</body>\n</html>\n")
        
    def send_html_file(self,file=None):
        """Send an HTML file as response"""
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self.end_headers()
        f = open(file,'r')
        self.wfile.write( f.read() )

    def send_top_level_index_page(self):
        """Send an HTML top-level index page as response"""
        title = "iiif_testserver on %s:%s" % (IIIFRequestHandler.HOST,IIIFRequestHandler.PORT)
        body = "<ul>\n"
        for prefix in sorted(IIIFRequestHandler.MANIPULATORS.keys()):
            body += '<li><a href="%s">%s</a></li>\n' % (prefix,prefix)
        body += "</ul>\n"
        return self.send_html_page( title, body )

    def send_prefix_index_page(self, prefix):
        """Send an HTML index page for a specific prefix as response"""
        title = "Prefix %s  (from iiif_testserver on %s:%s)" % (prefix,IIIFRequestHandler.HOST,IIIFRequestHandler.PORT)
        files = os.listdir(IIIFRequestHandler.IMAGE_DIR)
        api_version = IIIFRequestHandler.MANIPULATORS[prefix]['api_version']
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
        return self.send_html_page( title, body )
    
    def send_json_response(self, json, status=200):
        """ Send a JSON response 
        """
        self.send_response(status)
        self.send_header('Content-Type',self.json_mime_type)
        self.add_compliance_header()
        self.add_cors_header()
        if (status==401):
            self.send_header('WWW-Authenticate','Basic realm="This is HTTP Auth"')
        self.end_headers()
        self.wfile.write(json+"\n") #add CR at end for clarity

    def write_error_response(self,e):
        """ Write response for an IIIFError e

        Looks also to see whether an extra attribute e.headers is set to
        a dict with extra header fields
        """
        self.send_response(e.code)
        for header in e.headers:
            self.send_header(header,e.headers[header])
        self.send_header('Content-Type',e.content_type)
        self.add_compliance_header()
        self.end_headers()
        self.wfile.write(str(e))

    def add_cors_header(self):
        """All responses should have CORS header"""
        self.send_header('Access-control-allow-origin','*')

    def add_compliance_header(self):
        if (self.compliance_level is not None):
            self.send_header('Link','<'+self.compliance_level+'>;rel="compliesTo"')
        
    def do_GET(self):
        """Implement the HTTP GET method

        The bulk of this code is wrapped in a big try block and anywhere
        within the code may raise an IIIFError which then results in an
        IIIF error response (section 5 of spec).
        """
        self.compliance_level=None
        # We take prefix to see whe implementation to use, / is special info
        if (self.path == '/'):
            return self.send_top_level_index_page()
        
        # Test code...
        m = re.match(r'/response_test/(\d\d\d)$', self.path)
        if (m):
            status=int(m.group(1))
            # WHAT DOES NULL info.json look like?
            # https://github.com/IIIF/auth/issues/2
            self.api_version='2.0'
            i = IIIFInfo(api_version=self.api_version)
            i.identifier = 'abc'
            i.width = 0
            i.height = 0
            i.auth_uri = "http://example.com/authn_here"
            i.service = { '@context': 'http://example.org/auth_context.json',
                          '@id': i.auth_uri,
                          'label': "Authenticate here" }
            return self.send_json_response(json=i.as_json(),status=status)

        # Is this a request for a prefix index page?
        m = re.match(r'/([\w\._]+)$', self.path)
        if (m and m.group(1) in IIIFRequestHandler.MANIPULATORS):
            return self.send_prefix_index_page(m.group(1))

        # Is this a request for a test page?
        m = re.match(r'/([\w\._]+)$', self.path)
        if (m):
            page_path = os.path.join(IIIFRequestHandler.PAGES_DIR,m.group(1))
            if (os.path.isfile(page_path)):
                return self.send_html_file(page_path)

        # Now assume we have an iiif request
        m = re.match(r'/([\w\._]+)/(.*)$', self.path)
        if (m):
            self.prefix = m.group(1)
            self.path = m.group(2)
            if (self.prefix in IIIFRequestHandler.MANIPULATORS):
                self.api_version = IIIFRequestHandler.MANIPULATORS[self.prefix]['api_version']
                self.iiif = IIIFRequest(baseurl='/'+self.prefix+'/',api_version=self.api_version)
                self.manipulator = IIIFRequestHandler.MANIPULATORS[self.prefix]['klass'](api_version=self.api_version)
            else:
                # 404 - unrecognized prefix
                self.send_404_response("Not Found - prefix /%s/ is not known" % (self.prefix))
                return
        else:
            # 404 - unrecognized path structure
            self.send_404_response("Not Found - path structure not recognized")
            return
        try:
            (of,mime_type) = self.do_GET_body()
            if (not of):
                raise IIIFError("Unexpected failure to open result image")
            self.send_response(200)
            if (mime_type is not None):
                self.send_header('Content-Type',mime_type)
#            download_filename = os.path.basename(self.iiif.identifier)
#            if (self.iiif.ouput_format):
#                downlocal_filename += '.' + self.iiif.ouput_format 
#            self.send_header('Content-Disposition','inline;filename='+download_filename)
            self.add_compliance_header()
            self.add_cors_header()
            self.end_headers()
            while (1):
                buffer = of.read(8192)
                if (not buffer):
                    break
                self.wfile.write(buffer)
        except IIIFError as e:
            e.text += " Request parameters: "+str(self.iiif)
            self.write_error_response(e)
        except Exception as ue:
            # Anything else becomes a 500 Internal Server Error
            sys.stderr.write(str(ue)+"\n")
            self.write_error_response(IIIFError(code=500,text="Something went wrong... %s.\n"%(str(ue))))

    def do_GET_body(self):
        iiif=self.iiif
        if (len(self.path)>1024):
            raise IIIFError(code=414,
                            text="URI Too Long: Max 1024 chars, got %d\n" % len(self.path))
        #print "GET " + self.path
        try:
            iiif.parse_url(self.path)
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
        # URL path parsed OK, now determine how to handle request
        if (re.match('[\w\.\-]+$',iiif.identifier)):
            file = os.path.join(IIIFRequestHandler.IMAGE_DIR,iiif.identifier)
            if (not os.path.isfile(file)):
                images_available=""
                for image_file in os.listdir(IIIFRequestHandler.IMAGE_DIR):
                    if (os.path.isfile(os.path.join(IIIFRequestHandler.IMAGE_DIR,image_file))):
                        images_available += "  "+image_file+"\n"
                raise IIIFError(code=404,parameter="identifier",
                                text="Image resource '"+iiif.identifier+"' not found. Local image files available:\n" + images_available)
        else:
            raise IIIFError(code=404,parameter="identifier",
                            text="Image resource '"+iiif.identifier+"' not found. Only local test images and http: URIs for images are supported.\n")
        # 
        self.compliance_level=self.manipulator.complianceLevel
        if (self.iiif.info):
            # get size
            self.manipulator.srcfile=file
            self.manipulator.do_first()
            # most of info.json comes from config, a few things specific to image
            i = IIIFInfo(conf=IIIFRequestHandler.INFO,api_version=self.api_version)
            i.server_and_prefix = self.server_and_prefix
            i.identifier = self.iiif.identifier
            i.width = self.manipulator.width
            i.height = self.manipulator.height
            import StringIO
            return(StringIO.StringIO(i.as_json()),self.json_mime_type)
        else:
            if (self.api_version<'2.0' and
                self.iiif.format is None and
                'Accept' in self.headers):
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
            (outfile,mime_type)=self.manipulator.derive(file,iiif)
            return(open(outfile,'r'),mime_type)

def run(host='localhost', port=8888, 
        image_dir=None, pages_dir=None, info=None,
        server_class=BaseHTTPServer.HTTPServer,
        handler_class=IIIFRequestHandler):
    """Run webserver forever

    Conf must include Defaults to localhost, port, image_dir and info (a dict)
    """
    httpd = server_class( (host,port), handler_class)
    handler_class.HOST=host
    handler_class.PORT=port
    handler_class.IMAGE_DIR=image_dir
    handler_class.PAGES_DIR=pages_dir
    handler_class.INFO=info
    print "Starting webserver on %s:%d\n" % (host,port)
    httpd.serve_forever()

def main():
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
    p.add_option('--verbose', '-v', action='store_true',
                 help="Be verbose")
    p.add_option('--quiet','-q', action='store_true',
                 help="Minimal output only")
    (opt, args) = p.parse_args()

    if (opt.quiet):
        # Add no_op function as logger to silence
        IIIFRequestHandler.log_message=no_op

    # Import a set of manipulators and define prefixes for them
    versions = ['1.0', '1.1', '2.0']
    klass_names = ['pil','netpbm','dummy']
    auth_types = ['none']
    for api_version in versions:
        for klass_name in klass_names:
            for auth_type in auth_types:
                prefix = "%s_%s_%s" % (api_version,klass_name,auth_type)

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
                IIIFRequestHandler.add_manipulator( prefix, klass=klass, api_version=api_version, auth_type=auth_type )

    info={'tile_height': opt.tile_height,
          'tile_width': opt.tile_width,
          'qualities' : [ "native", "color" ],
          'scale_factors' : [1,2,4,8],
          'formats' : [ "jpg", "png" ]
    }
    for option in info:
        print "got %s = %s" % (option,info[option])
    #print "info = " + str(info)

    pidfile=os.path.basename(__file__)[:-3]+'.pid' #strip .py, add .pid
    with open(pidfile,'w') as fh:
        fh.write("%d\n" % os.getpid())
        fh.close()

    run(host=opt.host,
        port=opt.port,
        image_dir=opt.image_dir,
        pages_dir=opt.pages_dir,
        info=info)

if __name__ == "__main__":
    main()

