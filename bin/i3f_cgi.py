#!/usr/bin/env python2.7
"""Crude webserver that service i3f requests

Relies upon I3fManupulator object to do any manipulations
requested.
"""

import BaseHTTPServer
import re
import sys
import os
import os.path
import traceback

# These will likely need to be change for any installation
HOME_DIR = os.path.normpath(os.path.join(os.getcwd(),'..'))
TMP_DIR = os.path.join(HOME_DIR,'tmp')
TESTIMAGE_DIR = os.path.join(HOME_DIR,'i3f/testimages')
PNM_DIR = os.path.join(HOME_DIR,'opt/usr/bin')
SHELL_SETUP = 'export LD_LIBRARY_PATH='+os.path.join(HOME_DIR,'opt/usr/lib')+'; ';

from i3f.error import I3fError
from i3f.request import I3fRequest

class I3fRequestException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class CGI_responder(object):
    def send_response(self,code,text=''):
        print "Status: %s %s\r" % (str(code),text)

    def send_header(self,header,value):
        print "%s: %s\r" % (header,value)

    def end_headers(self):
        print "\r"

    
#class I3fRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
class I3fRequestHandler(CGI_responder):

    """Class variable as dictionary of named profiles

    In this server we implement named profiles as a dictionary
    of I3f objects which specify parameterized requests indexed
    by profile name. This limits named profiles to things that
    can be specified as a parameterized request. The specification
    has no such limitation.
    """
    named_profiles={ }
    manipulator_class=None

    @classmethod
    def loadProfile(cls,profile,i3f_request_attributes):
        """Load a named profile into the I3fRequestHandler class
        """
        cls.named_profiles[profile]=i3f_request_attributes

       
#    def __init__(self, request, client_address, server):
    def __init__(self):
        # Add some local attributes for this subclass (seems we have to 
        # do this ahead of calling the base class __init__ because that
        # does not return
        self.debug=True
        self.complianceLevel=None;
        # Cannot use super() because BaseHTTPServer.BaseHTTPRequestHandler 
        # is not new style class
        #super(I3fRequestHandler, self).__init__(request, client_address, server)
        #BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
        self.path= ( os.environ['PATH_INFO'] if ('PATH_INFO' in os.environ) else '/bogus')
        self.wfile=sys.stdout

    """Minimal implementation of HTTP request handler to do i3f GET
    """
    def error_response(self,code,content=''):
        self.send_response(code)
        self.send_header('Content-Type','text/xml')
        self.add_compliance_header()
        self.end_headers()
        self.wfile.write(content)

    def add_compliance_header(self):
        if (self.complianceLevel is not None):
            self.send_header('Link','<'+self.complianceLevel+'>;rel="compliesTo"')
        
    def do_GET(self):
        """Implement the HTTP GET method

        The bulk of this code is wrapped in a big try block and anywhere
        within the code may raise an I3fError which then results in an
        I3f error response (section 5 of spec).
        """
        self.complianceLevel=None
        self.i3f = I3fRequest(baseurl='/')
        try:
            (of,mime_type) = self.do_GET_body()
            if (not of):
                raise I3fError("Unexpected failure to open result image")
            self.send_response(200,'OK')
            if (mime_type is not None):
                self.send_header('Content-Type',mime_type)
            self.add_compliance_header()
            self.end_headers()
            while (1):
                buffer = of.read(8192)
                if (not buffer):
                    break
                self.wfile.write(buffer)
            # Now cleanup
            self.manipulator.cleanup()
        except I3fError as e:
            if (self.debug):
                e.text += "\nRequest parameters:\n" + str(self.i3f)
            self.error_response(e.code, str(e))
        except Exception as ue:
            # Anything else becomes a 500 Internal Server Error
            e = I3fError(code=500,text="Something went wrong... %s ---- %s.\n"%(str(ue),traceback.format_exc()))
            if (self.debug):
                e.text += "\nRequest parameters:\n" + str(self.i3f)
            self.error_response(e.code, str(e))

    def do_GET_body(self):
        i3f=self.i3f
        if (len(self.path)>1024):
            raise I3fError(code=414,
                           text="URI Too Long: Max 1024 chars, got %d\n" % len(self.path))
        #   print "GET " + self.path
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
        if (i3f.profile is not None):
            # this is named-profile request
            if (i3f.profile in self.named_profiles):
                # substitute named-profile parameters for current request
                id = i3f.identifier
                i3f.parse_url('/dummyid'+self.named_profiles[i3f.profile])
                i3f.identifier = id
            else:
                raise I3fError(code=400,
                               text="Named-profile %s not implemented" % (i3f.profile) )
        # Now we have a full i3f request either through direct specification
        # of parameters or through translation of a named-profile request
        if (re.match('[\w\.\-]+$',i3f.identifier)):
            file = os.path.join(TESTIMAGE_DIR,i3f.identifier)
            if (not os.path.isfile(file)):
                images_available=""
                for image_file in os.listdir(TESTIMAGE_DIR):
                    if (os.path.isfile(os.path.join(TESTIMAGE_DIR,image_file))):
                        images_available += "  "+image_file+"\n"
                raise I3fError(code=404,parameter="identifier",
                               text="Image resource '"+i3f.identifier+"' not found. Local image files available:\n" + images_available)
        else:
            raise I3fError(code=404,parameter="identifier",
                           text="Image resource '"+i3f.identifier+"' not found. Only local test images and http: URIs for images are supported.\n")
        manipulator = I3fRequestHandler.manipulator_class()
        self.complianceLevel=manipulator.complianceLevel;
        (outfile,mime_type)=manipulator.do_i3f_manipulation(file,i3f)
        # Stash manipulator object so we can cleanup after reading file
        self.manipulator=manipulator
        return(open(outfile,'r'),mime_type)
               
I3fRequestHandler.loadProfile( 'unmodified', '/full/pct:100/0/color' )
I3fRequestHandler.loadProfile( 'thumb', '/full/!32,32/0/color' )

#print "Content-type: text/plain\r\n\r"
#print "hello"
#exit(0)
myname = ( os.environ['SCRIPT_NAME'] if ('SCRIPT_NAME' in os.environ) else '/i3f_dummy.cgi')
sys.stderr = sys.stdout
if (myname == '/i3f_dummy.cgi'):
    from i3f.manipulator_dummy import I3fManipulatorDummy
    I3fRequestHandler.manipulator_class = I3fManipulatorDummy
elif (myname == '/i3f_netpbm.cgi'):
    from i3f.manipulator_netpbm import I3fManipulatorNetpbm
    I3fManipulatorNetpbm.find_binaries(tmpdir=TMP_DIR,
                                       shellsetup=SHELL_SETUP,
                                       pnmdir=PNM_DIR)
    I3fRequestHandler.manipulator_class = I3fManipulatorNetpbm
elif (myname == '/i3f_pil.cgi'):
    from i3f.manipulator_pil import I3fManipulatorPIL
    I3fRequestHandler.manipulator_class = I3fManipulatorPIL
else:
    print "Status: 500\r"
    print "Content-type: text/plain\r\n\r"
    print "Bad script name '%s'" % myname
    exit(0)

rh = I3fRequestHandler()
rh.do_GET()
