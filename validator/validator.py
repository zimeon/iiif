
from functools import partial
from bottle import Bottle, route, run, request, response, abort, error

# Black Module Magic to get tests in the right place
import tests
from tests import *
all_tests = tests.__all__
g = globals()
for t in all_tests:
    setattr(tests, t, g[t])
    del globals()[t]

from tests.test import ValidatorError

import urllib2
import json
import StringIO
import sys
import random
import os

try:
    from PIL import Image, ImageDraw
except:
    import Image, ImageDraw

class ValidationInfo(object):
    def __init__(self):

        self.mimetypes = {'bmp' : 'image/bmp',  
                   'gif' : 'image/gif', 
                   'jpg': 'image/jpeg', 
                   'pcx' : 'image/pcx', 
                   'pdf' :  'application/pdf', 
                   'png' : 'image/png', 
                   'tif' : 'image/tiff',
                   'webp' : 'image/webp'}

        self.pil_formats = {'BMP' : 'image/bmp',  
                   'GIF' : 'image/gif', 
                   'JPEG': 'image/jpeg', 
                   'PCX' : 'image/pcx', 
                   'PDF' :  'application/pdf', 
                   'PNG' : 'image/png', 
                   'TIFF' : 'image/tiff'}
        
        self.colorInfo = [[(61, 170, 126), (61, 107, 178), (82, 85, 234), (164, 122, 110), (129, 226, 88), (91, 37, 121), (138, 128, 42), (6, 85, 234), (121, 109, 204), (65, 246, 84)], 
            [(195, 133, 120), (171, 43, 102), (118, 45, 130), (242, 105, 171), (5, 85, 105), (113, 58, 41), (223, 69, 3), (45, 79, 140), (35, 117, 248), (121, 156, 184)], 
            [(168, 92, 163), (28, 91, 143), (86, 41, 173), (111, 230, 29), (174, 189, 7), (18, 139, 88), (93, 168, 128), (35, 2, 14), (204, 105, 137), (18, 86, 128)], 
            [(107, 55, 178), (251, 40, 184), (47, 36, 139), (2, 127, 170), (224, 12, 114), (133, 67, 108), (239, 174, 209), (85, 29, 156), (8, 55, 188), (240, 125, 7)], 
            [(112, 167, 30), (166, 63, 161), (232, 227, 23), (74, 80, 135), (79, 97, 47), (145, 160, 80), (45, 160, 79), (12, 54, 215), (203, 83, 70), (78, 28, 46)], 
            [(102, 193, 63), (225, 55, 91), (107, 194, 147), (167, 24, 95), (249, 214, 96), (167, 34, 136), (53, 254, 209), (172, 222, 21), (153, 77, 51), (137, 39, 183)], 
            [(159, 182, 192), (128, 252, 173), (148, 162, 90), (192, 165, 115), (154, 102, 2), (107, 237, 62), (111, 236, 219), (129, 113, 172), (239, 204, 166), (60, 96, 37)], 
            [(72, 172, 227), (119, 51, 100), (209, 85, 165), (87, 172, 159), (188, 42, 162), (99, 3, 54), (7, 42, 37), (105, 155, 100), (38, 220, 240), (98, 46, 2)], 
            [(18, 223, 145), (189, 121, 17), (88, 3, 210), (181, 16, 43), (189, 39, 244), (123, 147, 116), (246, 148, 214), (223, 177, 199), (77, 18, 136), (235, 36, 21)], 
            [(146, 137, 176), (84, 248, 55), (61, 144, 79), (110, 251, 49), (43, 105, 132), (165, 131, 55), (60, 23, 225), (147, 197, 226), (80, 67, 104), (161, 119, 182)]]
  
    def do_test_square(self, img, x,y, result):
        truth = self.colorInfo[x][y]
        # Similarity, not necessarily perceived
        cols = img.getcolors()
        cols.sort(reverse=True)
        col = cols[0][1]
        ok = abs(col[0]-truth[0]) < 6 and abs(col[1]-truth[1]) < 6 and abs(col[2]-truth[2]) < 6
        result.tests.append("%s,%s:%s" % (x,y,ok))
        return ok           

    def make_randomstring(self, length):
        stuff = []
        for x in range(length):
            stuff.append(chr(random.randint(48, 122)))    
        val = ''.join(stuff)
        # prevent end-of-path-segment characters
        val = val.replace('?', '$')
        val = val.replace('#', '$')
        val = val.replace('/', '$')
        return val

    def check(self, typ, got, expected, result=None):
        if type(expected) == list:
            if not got in expected:
                raise ValidatorError(typ, got, expected, result)
        elif got != expected:
            raise ValidatorError(typ, got, expected, result)
        if result:
            result.tests.append(typ)
        return 1

        
class TestSuite(object):

    def __init__(self, info):
        self.validationInfo = info

    def has_test(self, test):
        return hasattr(tests, test)
          
    def list_tests(self, version=""):
        allt = {}
        for t in all_tests:
            testm = getattr(tests, t)  # Module
            oname = "test_%s" % t
            oname = oname.replace("_", " ").title().replace(" ", "_")
            testc = getattr(testm, oname) # Class
            data = testc.make_info(version)
            if data:
                allt[t] = data
        return allt

    def run_test(self, test, result):   

        testm = getattr(tests, test)
        oname = "test_%s" % test
        oname = oname.replace("_", " ").title().replace(" ", "_")
        testc = getattr(testm, oname)
        test = testc(self.validationInfo)

        result.test_info = test.make_info(result.version)

        try:
            return test.run(result)
        except ValidatorError, e:
            result.exception = e
            return result
 
class ImageAPI(object):

    def __init__(self, identifier, server, prefix="", scheme="http", auth="", version="2.0", debug=True):

        self.iiifNS = "{http://library.stanford.edu/iiif/image-api/ns/}"
        self.debug = debug

        self.scheme = scheme
        self.server = server
        if not prefix:
            self.prefix = ""
        else:
            self.prefix = prefix.split('/')
        self.identifier = identifier
        self.auth = auth

        self.version = version

        self.last_headers = {}
        self.last_status = 0
        self.last_url = ''

        # DOUBLE duty as result object
        self.name = ""
        self.urls = []
        self.tests = []
        self.exception = None

    def parse_links(self, header):

        state = 'start'
        header = header.strip()
        data = [d for d in header]
        links = {}
        while data:
            if state == 'start':
                d = data.pop(0)
                while d.isspace():
                    d = data.pop(0)
                if d != "<":
                    raise ValueError("Parsing Link Header: Expected < in start, got %s" % d)                    
                state = "uri"
            elif state == "uri":
                uri = []
                d = data.pop(0)                
                while d != ";":
                    uri.append(d)
                    d = data.pop(0)
                uri = ''.join(uri)
                uri = uri[:-1]
                data.insert(0, ';')
                # Not an error to have the same URI multiple times (I think!)
                if not links.has_key(uri):
                    links[uri] = {}
                state = "paramstart"
            elif state == 'paramstart':
                d = data.pop(0)
                while data and d.isspace():
                    d = data.pop(0)
                if d == ";":
                    state = 'linkparam';
                elif d == ',':
                    state = 'start'
                else:
                    raise ValueError("Parsing Link Header: Expected ; in paramstart, got %s" % d)
                    return
            elif state == 'linkparam':
                d = data.pop(0)
                while d.isspace():
                    d = data.pop(0)
                paramType = []
                while not d.isspace() and d != "=":
                    paramType.append(d)
                    d = data.pop(0)
                while d.isspace():
                    d = data.pop(0)
                if d != "=":
                    raise ValueError("Parsing Link Header: Expected = in linkparam, got %s" % d)
                    return
                state='linkvalue'
                pt = ''.join(paramType)
                if not links[uri].has_key(pt):
                    links[uri][pt] = []
            elif state == 'linkvalue':
                d = data.pop(0)
                while d.isspace():
                    d = data.pop(0)
                paramValue = []
                if d == '"':
                    pd = d
                    d = data.pop(0)
                    while d != '"' and pd != '\\':
                        paramValue.append(d)
                        pd = d
                        d = data.pop(0)
                else:
                    while not d.isspace() and not d in (',', ';'):
                        paramValue.append(d)
                        if data:
                            d = data.pop(0)
                        else:
                            break
                    if data:
                        data.insert(0, d)
                state = 'paramstart'
                pv = ''.join(paramValue)
                if pt == 'rel':
                    # rel types are case insensitive and space separated
                    links[uri][pt].extend([y.lower() for y in pv.split(' ')])
                else:
                    if not pv in links[uri][pt]:
                        links[uri][pt].append(pv)
        return links


    def get_uri_for_rel(self, links, rel):
        rel = rel.lower()
        for (uri, info) in links.items():
            rels = info.get('rel', [])
            if rel in rels:
                return uri
        return None

    def fetch(self, url):
        # print url
        try:
            wh = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            wh = e
        except:
            raise 
        data = wh.read()
        # nasty side effect
        self.last_headers = wh.headers.dict
        self.last_status = wh.code
        self.last_url = url
        wh.close()
        self.urls.append(url)
        return(data)

    def make_url(self, params={}):
        if self.prefix and not params.has_key('prefix'):
            params['prefix'] = self.prefix
        if not params.has_key('identifier'):
            params['identifier'] = self.identifier
        if not params.has_key('region'):
            params['region'] = 'full'
        if not params.has_key('size'):
            params['size'] = 'full'
        if not params.has_key('rotation'):
            params['rotation'] = '0'
        if not params.has_key('quality'):
            if self.version == "2.0":
                params['quality'] = 'default'
            else:
                params['quality'] = 'native'        
        elif params['quality'] == 'grey' and self.version == "2.0":
            # en-us in 2.0+
            params['quality'] = 'gray'
        if not params.has_key('format') and self.version == "2.0":
            # format is required in 2.0+
            params['format'] = 'jpg'

        order = ('prefix','identifier','region','size','rotation','quality')

        if 'prefix' in params:
            params['prefix'] = '/'.join(self.prefix)
        url = '/'.join(params.get(p) for p in order if params.get(p) is not None)

        if params.get('format') is not None:
            url+='.%s' % params['format']

        scheme = params.get('scheme', self.scheme)
        server = params.get('server', self.server)
        url = "%s://%s/%s" % (scheme, server, url)
        if (self.debug):
            print url
        return url

    def make_image(self, data):
        imgio = StringIO.StringIO(data)
        img = Image.open(imgio)
        return img

    def get_image(self, params):
        url = self.make_url(params)
        imgdata = self.fetch(url)
        img = self.make_image(imgdata)
        return img

    def make_info_url(self, format='json'):
        params = {'server':self.server, 'identifier':self.identifier, 'scheme':self.scheme}
        if self.prefix:
            parts = self.prefix[:]
        else:
            parts = []
        parts.extend([self.identifier, 'info'])
        url = '%s.%s' %  ('/'.join(parts), format)
        scheme = params.get('scheme', self.scheme)
        server = params.get('server', self.server)
        url = "%s://%s/%s" % (self.scheme, self.server, url)
        return url

    def get_info(self):
        url = self.make_info_url()
        try:
            idata = self.fetch(url) 
        except:
            # uhoh
            return None
        try:
            info = json.loads(idata)
        except:
            return None
        return info


class Validator(object):

    def __init__(self,debug=True):
        if (debug):
            sys.stderr.write('init on Validator\n')
            sys.stderr.flush()

    def handle_test(self, testname):

        version = request.query.get('version', '2.0')
        info = ValidationInfo()
        testSuite = TestSuite(info)

        if testname == "list_tests":
            tests = testSuite.list_tests(version)
            return json.dumps(tests)
        if not testSuite.has_test(testname):
            return "No such test: %s" % testname

        server = request.query.get('server', '')
        server = server.strip()
        if server.startswith('https://'):
            scheme = 'https'
            server = server.replace('https://', '')
        else:
            scheme="http"
            server = server.replace('http://', '')  
        atidx = server.find('@') 
        if atidx > -1:
            auth = server[:atidx]
            server = server[atidx+1:]
        else:
            auth = ""
        if not server:
            return "Missing mandatory parameter: server"

        if server[-1] == '/':
            server = server[:-1]

        prefix = request.query.get('prefix', '')
        prefix = prefix.strip()
        if prefix:
            prefix = prefix.replace('%2F', '/')
            if prefix[-1] == '/':
                prefix = prefix[:-1]
            if prefix[0] == '/':
                prefix = prefix[1:]

        identifier = request.query.get('identifier', '')
        identifier = identifier.strip()
        if not identifier:
            return "Missing mandatory parameter: identifier"

        try:
            result = ImageAPI(identifier, server, prefix, scheme, auth, version)

            testSuite.run_test(testname, result)
            if result.exception:
                e = result.exception
                info = {'test' : testname, 'status': 'error', 'url':result.urls, 'got':e.got, 'expected': e.expected, 'type': e.type}
            else:
                info = {'test' : testname, 'status': 'success', 'url':result.urls, 'tests':result.tests}
            if result.test_info:
                info['label'] = result.test_info['label']

        except Exception, e:
            raise
            info = {'test' : testname, 'status': 'internal-error', 'url':e.url, 'msg':str(e)}
        infojson = json.dumps(info)
        return infojson
  
    def dispatch_views(self):
        pfx = ""
        self.app.route("/%s<testname>" % pfx, "GET", self.handle_test)

    def after_request(self):
        """A bottle hook for json responses."""
        response["content_type"] = "application/json"
        methods = 'GET'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        # Already added by apache config
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers
        response.headers['Allow'] = methods


    def not_implemented(self, *args, **kwargs):
        """Returns not implemented status."""
        abort(501)

    def empty_response(self, *args, **kwargs):
        """Empty response"""

    options_list = empty_response
    options_detail = empty_response


    def error(self, error, message=None):
        """Returns the error response."""
        return self._jsonify({"error": error.status_code,
                        "message": error.body or message}, "")

    def get_error_handler(self):
        """Customized errors"""
        return {
            500: partial(self.error, message="Internal Server Error."),
            404: partial(self.error, message="Document Not Found."),
            501: partial(self.error, message="Not Implemented."),
            405: partial(self.error, message="Method Not Allowed."),
            403: partial(self.error, message="Forbidden."),
            400: self.error
        }

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        self.app.error_handler = self.get_error_handler()
        return self.app


def apache():
    v = Validator()
    return v.get_bottle_app()

def main():
    mr = Validator()
    run(host='localhost', reloader=True, port=8080, app=mr.get_bottle_app())


if __name__ == "__main__":
    main()
elif (not os.getenv('VALIDATOR_AS_MODULE')):
    application = apache()
