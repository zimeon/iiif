#!/usr/bin/env python
"""Crude webserver that services IIIF Image API requests

Relies upon IIIFManipulator object to do any manipulations
requested.
"""

import BaseHTTPServer
import re
import os
import os.path

from iiif.config import IIIFConfig
from iiif.error import IIIFError
from iiif.request import IIIFRequest
from iiif.info import IIIFInfo

class IIIFRequestException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class IIIFRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    # Class data
    HOST=None
    PORT=None
    IMAGE_DIR=None
    INFO=None
    MANIPULATORS={}
    
    @classmethod
    def add_manipulator(cls, prefix, klass, api_version='2.0'):
        cls.MANIPULATORS[prefix]={'klass': klass, 'api_version': api_version}

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

    def send_404_response(self, content='Resource Not Found'):
        """Send a plain 404 for URLs not under a known IIIF endpoint prefix"""
        self.send_response(404)
        self.send_header('Content-Type','text/plain')
        self.end_headers()
        self.wfile.write(content)
    
    def send_index_page(self, file='index.html'):
        """Send an HTML file as response"""
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self.end_headers()
        self.wfile.write("<html><head><title>iiif_testserver</title></head><body>\n")
        self.wfile.write("<h1>iiif_testserver on %s:%s</h1>\n" %(IIIFRequestHandler.HOST,IIIFRequestHandler.PORT))
        prefixes = sorted(IIIFRequestHandler.MANIPULATORS.keys())
        files = os.listdir(IIIFRequestHandler.IMAGE_DIR)
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
        
    """Minimal implementation of HTTP request handler to do iiif GET
    """
    def error_response(self,code,content=''):
        self.send_response(code)
        self.send_header('Content-Type','text/xml')
        self.add_compliance_header()
        self.end_headers()
        self.wfile.write(content)

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
            self.send_index_page()
            return
        # Now assume we have an iiif request
        m = re.match(r'/([\w\._]+)/(.*)$', self.path)
        if (m):
            prefix = m.group(1)
            self.path = m.group(2)
            if (prefix in IIIFRequestHandler.MANIPULATORS):
                v = IIIFRequestHandler.MANIPULATORS[prefix]['api_version']
                self.iiif = IIIFRequest(baseurl='/'+prefix+'/',api_version=v)
                self.manipulator = IIIFRequestHandler.MANIPULATORS[prefix]['klass'](api_version=v)
            else:
                # 404 - unrecognized prefix
                self.send_404_response("Not Found - prefix /%s/ is not known" % (prefix))
                return
        else:
            # 404 - unrecognized path structure
            self.send_404_response("Not Found - path structure not recognized")
            return
        try:
            (of,mime_type) = self.do_GET_body()
            if (not of):
                raise IIIFError("Unexpected failure to open result image")
            self.send_response(200,'OK')
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
            if (self.debug):
                e.text += " Request parameters: " + str(self.iiif)
            self.error_response(e.code, str(e))
        except Exception as ue:
            # Anything else becomes a 500 Internal Server Error
            e = IIIFError(code=500,text="Something went wrong... %s.\n"%(str(ue)))
            if (self.debug):
                e.text += " Request parameters: " + str(self.iiif)
            self.error_response(e.code, str(e))

    def do_GET_body(self):
        iiif=self.iiif
        if (len(self.path)>1024):
            raise IIIFError(code=414,
                            text="URI Too Long: Max 1024 chars, got %d\n" % len(self.path))
        print "GET " + self.path
        try:
            iiif.parse_url(self.path)
        except IIIFRequestException as e:
            # Most conditions would thow an IIIFError which is handled
            # elsewhere, catch others and rethrow
            raise IIIFError(code=400,
                           text="Bad request: " + str(e) + "\n") 
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
            i = IIIFInfo(conf=IIIFRequestHandler.INFO)
            i.identifier = self.iiif.identifier
            i.width = self.manipulator.width
            i.height = self.manipulator.height
            import StringIO
            return(StringIO.StringIO(i.as_json()),"application/json")
        else:
            (outfile,mime_type)=self.manipulator.derive(file,iiif)
            return(open(outfile,'r'),mime_type)

def run(host='', port=8888, image_dir='img', info=None,
        server_class=BaseHTTPServer.HTTPServer,
        handler_class=IIIFRequestHandler):
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

conf = IIIFConfig()
# Import a set of manipulators and define prefixes for them
for section in conf.get_test_sections():
    prefix = conf.get(section,'prefix')
    if (prefix.find('/')>=0):
        print "Prefix must not contain slash, %s in section %s ignored" % (prefix,section)
        continue
    klass_name = conf.get(section,'klass')
    api_version = conf.get(section,'api_version')
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
        print "Unknown manipulator type %s in section %s, ignoring" % (klass_name,section)
        continue
    print "Installing %s IIIFManipulator at /%s/ v%s" % (klass_name,prefix,api_version)
    IIIFRequestHandler.add_manipulator( prefix, klass=klass, api_version=api_version )

info={}
for option in conf.conf.options('info'):
    print "got %s = %s" % (option,conf.get('info',option))
    info[option] = conf.get('info',option)
print "info = " + str(info)

run(host=conf.get('test_server','server_host'),
    port=int(conf.get('test_server','server_port')),
    image_dir=conf.get('test_server','image_dir'),
    info=info)
