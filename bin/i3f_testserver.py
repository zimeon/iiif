#!/usr/bin/env python
"""Crude webserver that service i3f requests

Relies upon I3fManupulator object to do any manipulations
requested.
"""

import BaseHTTPServer
import re
import os
import os.path

from i3f.config import I3fConfig
from i3f.error import I3fError
from i3f.request import I3fRequest
from i3f.info import I3fInfo

class I3fRequestException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class I3fRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    # Class data
    HOST=None
    PORT=None
    IMAGE_DIR=None
    INFO=None
    MANIPULATOR_CLASSES={}
    
    @classmethod
    def add_manipulator(cls, klass,prefix):
        cls.MANIPULATOR_CLASSES[prefix]=klass

    def __init__(self, request, client_address, server):
        # Add some local attributes for this subclass (seems we have to 
        # do this ahead of calling the base class __init__ because that
        # does not return
        self.debug=True
        self.compliance_level=None
        self.manipulator=None
        # Cannot use super() because BaseHTTPServer.BaseHTTPRequestHandler 
        # is not new style class
        #super(I3fRequestHandler, self).__init__(request, client_address, server)
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def send_404_response(self, content='Resource Not Found'):
        """Send a plain 404 for URLs not under a known IIIF endpoint prefix"""
        self.send_response(404)
        self.send_header('Content-Type','text/plain')
        self.end_headers()
        self.wfile.write(content)
    
    def send_index_page(self, file='index.html'):
        """Send an HTML file as response"""
        self.send_response(404)
        self.send_header('Content-Type','text/html')
        self.end_headers()
        self.wfile.write("<html><head><title>i3f_testserver</title></head><body>\n")
        self.wfile.write("<h1>i3f_testserver on %s:%s</h1>\n" %(I3fRequestHandler.HOST,I3fRequestHandler.PORT))
        prefixes = sorted(I3fRequestHandler.MANIPULATOR_CLASSES.keys())
        files = os.listdir(I3fRequestHandler.IMAGE_DIR)
        self.wfile.write("<table>\n")
        self.wfile.write("<tr><th></th>")
        for prefix in prefixes:
            self.wfile.write('<th colspan="2">%s</th>' % (prefix))
            if (prefix!='dummy'):
                self.wfile.write("<th>%s 256x256</th>" % (prefix))
        self.wfile.write("</tr>\n")
        for file in sorted(files):
            self.wfile.write("<tr><th>%s</th>" % (file))
            for prefix in prefixes:
                url = "/%s/%s/full/full/0/native" % (prefix,file)
                self.wfile.write('<td><a href="%s">%s</a></td>' % (url,url))
                info = "/%s/%s/info.json" % (prefix,file)
                self.wfile.write('<td><a href="%s">%s</a></td>' % (info,info))
                if (prefix!='dummy'):
                    url = "/%s/%s/full/256,256/0/native" % (prefix,file)
                    self.wfile.write('<td><a href="%s">%s</a></td>' % (url,url))
            self.wfile.write("</tr>\n")
        self.wfile.write("</table<\n")
        self.wfile.write("</html>\n")
        
    """Minimal implementation of HTTP request handler to do i3f GET
    """
    def error_response(self,code,content=''):
        self.send_response(code)
        self.send_header('Content-Type','text/xml')
        self.add_compliance_header()
        self.end_headers()
        self.wfile.write(content)

    def add_compliance_header(self):
        if (self.compliance_level is not None):
            self.send_header('Link','<'+self.compliance_level+'>;rel="compliesTo"')
        
    def do_GET(self):
        """Implement the HTTP GET method

        The bulk of this code is wrapped in a big try block and anywhere
        within the code may raise an I3fError which then results in an
        I3f error response (section 5 of spec).
        """
        self.compliance_level=None
        # We take prefix to see whe implementation to use, / is special info
        if (self.path == '/'):
            self.send_index_page()
            return
        # Now assume we have an iiif request
        m = re.match(r'/(\w+)(/.*)$', self.path)
        if (m):
            prefix = m.group(1)
            if (prefix in I3fRequestHandler.MANIPULATOR_CLASSES):
                self.i3f = I3fRequest(baseurl='/'+prefix+'/')
                self.manipulator = I3fRequestHandler.MANIPULATOR_CLASSES[prefix]()
            else:
                # 404 - unrecognized prefix
                self.send_404_response("Not Found - prefix /%s/ is not known" + (prefix))
                return
        else:
            # 404 - unknwn prefix/path structure
            self.send_404_response("Not Found - path structure not recognized")
            return
        try:
            (of,mime_type) = self.do_GET_body()
            if (not of):
                raise I3fError("Unexpected failure to open result image")
            self.send_response(200,'OK')
            if (mime_type is not None):
                self.send_header('Content-Type',mime_type)
#            download_filename = os.path.basename(self.i3f.identifier)
#            if (self.i3f.ouput_format):
#                downlocal_filename += '.' + self.i3f.ouput_format 
#            self.send_header('Content-Disposition','inline;filename='+download_filename)
            self.add_compliance_header()
            self.end_headers()
            while (1):
                buffer = of.read(8192)
                if (not buffer):
                    break
                self.wfile.write(buffer)
        except I3fError as e:
            if (self.debug):
                e.text += " Request parameters: " + str(self.i3f)
            self.error_response(e.code, str(e))
        except Exception as ue:
            # Anything else becomes a 500 Internal Server Error
            e = I3fError(code=500,text="Something went wrong... %s.\n"%(str(ue)))
            if (self.debug):
                e.text += " Request parameters: " + str(self.i3f)
            self.error_response(e.code, str(e))

    def do_GET_body(self):
        i3f=self.i3f
        if (len(self.path)>1024):
            raise I3fError(code=414,
                           text="URI Too Long: Max 1024 chars, got %d\n" % len(self.path))
        print "GET " + self.path
        try:
            i3f.parse_url(self.path)
        except I3fRequestException as e:
            # Most conditions would thow an I3fError which is handled
            # elsewhere, catch others and rethrow
            raise I3fError(code=400,
                           text="Bad request: " + str(e) + "\n") 
        except Exception as e:
            # Something completely unexpected => 500
            raise I3fError(code=500,
                           text="Internal Server Error: unexpected exception parsing request (" + str(e) + ")")
        # URL path parsed OK, now determine how to handle request
        if (re.match('[\w\.\-]+$',i3f.identifier)):
            file = os.path.join(I3fRequestHandler.IMAGE_DIR,i3f.identifier)
            if (not os.path.isfile(file)):
                images_available=""
                for image_file in os.listdir(I3fRequestHandler.IMAGE_DIR):
                    if (os.path.isfile(os.path.join(I3fRequestHandler.IMAGE_DIR,image_file))):
                        images_available += "  "+image_file+"\n"
                raise I3fError(code=404,parameter="identifier",
                               text="Image resource '"+i3f.identifier+"' not found. Local image files available:\n" + images_available)
        else:
            raise I3fError(code=404,parameter="identifier",
                           text="Image resource '"+i3f.identifier+"' not found. Only local test images and http: URIs for images are supported.\n")
        # 
        self.compliance_level=self.manipulator.complianceLevel
        if (self.i3f.info):
            # get size
            self.manipulator.srcfile=file
            self.manipulator.i3f=i3f
            self.manipulator.do_first()
            # most of info.json comes from config, a few things specific to image
            i = I3fInfo(conf=I3fRequestHandler.INFO)
            i.identifier = self.i3f.identifier
            i.width = self.manipulator.width
            i.height = self.manipulator.height
            import StringIO
            return(StringIO.StringIO(i.as_json()),"application/json")
        else:
            (outfile,mime_type)=self.manipulator.do_i3f_manipulation(file,i3f)
            return(open(outfile,'r'),mime_type)

def run(host='', port=8888, image_dir='img', info=None,
        server_class=BaseHTTPServer.HTTPServer,
        handler_class=I3fRequestHandler):
    """Run webserver forever

    Conf must include Defaults to localhost, port, image_dir and info (a dict)
    """
    httpd = server_class( (host,port), handler_class)
    handler_class.HOST=host
    handler_class.PORT=port
    handler_class.IMAGE_DIR=image_dir
    handler_class.INFO=info
    print "Starting webserver on %s:%d\n" % (host,port)
    httpd.serve_forever()

conf = I3fConfig()
# Import a set of manipulators and define prefixes for them
if (conf.get('test','run_dummy')):
    from i3f.manipulator import I3fManipulator
    prefix=prefix=conf.get('test','dummy_prefix')
    I3fRequestHandler.add_manipulator( klass=I3fManipulator,prefix=prefix )
    print "Installing I3fManipulator at /%s/" % (prefix)
if (conf.get('test','run_pil')):
    from i3f.manipulator_pil import I3fManipulatorPIL
    prefix=conf.get('test','pil_prefix')
    print "Installing I3fManipulatorPIL at /%s/" % (prefix)
    I3fRequestHandler.add_manipulator( klass=I3fManipulatorPIL,prefix=prefix )
if (conf.get('test','run_netpbm')):
    from i3f.manipulator_netpbm import I3fManipulatorNetpbm
    prefix=conf.get('test','netpbm_prefix')
    print "Installing I3fManipulatorNetpbm at /%s/" % (prefix)
    I3fRequestHandler.add_manipulator( klass=I3fManipulatorNetpbm,prefix=prefix )

info={}
for option in conf.conf.options('info'):
    print "got %s = %s" % (option,conf.get('info',option))
    info[option] = conf.get('info',option)
print "info = " + str(info)

run(host=conf.get('test','server_host'),
    port=int(conf.get('test','server_port')),
    image_dir=conf.get('test','image_dir'),
    info=info)
