import urllib
import re
import string

class I3fError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class I3f:
    """ http://server/[prefix/]identifier/region/rotation/size[/quality][.format]
    " or
    " http://server/[prefix/]identifier/named-profile[.format]
    """

    def __init__(self, **params):
        """ Create I3f object and optionally set any attribute via named parameters

        Unless specified the baseurl will be set to nothing ("").
        """
        self.clear()
        self.set(**params)

    def clear(self):
        self.baseurl = ""
        self.identifier = None
        self.region = None
        self.rotation = None
        self.size = None
        self.quality = None
        self.format = None
        self.profile = None

    def set(self, **params):
        # FIXME - maybe make this safe an allow only setting valid attributes
        self.__dict__.update(**params)

    def quote(self, path_segment):
        """ Quote all non UNRESERVED characters in the URI path segment
        "
        " Percent encode all characters not in the unreserved or sub-delims
        " sets as defined by RFC3986
        "
        " http://tools.ietf.org/html/rfc3986#section-2.3
        " reserved    = gen-delims / sub-delims
        " gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
        " sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
        "             / "*" / "+" / "," / ";" / "="
        " unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        """
        return( urllib.quote(path_segment,"-._~!$&'()*+,;=") )

    def url(self, **params):
        """ Build a URL path according to the IIIF API parameterized or named-profile form

        The parameterized form is assumed unless a profile parameter is specified.
        """
        self.set(**params)
        path = self.baseurl +\
            self.quote(self.identifier) + "/"
        if (self.profile):
            # named profile form
            path += self.quote(self.profile)
        else:
            # set defaults if not given
            region=self.region if self.region else "all"
            rotation=self.rotation if self.rotation else "0"
            size=self.size if self.size else "pct:100"
            # parameterized form (quality optional)
            path += self.quote(region) + "/" +\
                    self.quote(rotation) + "/" +\
                    self.quote(size)
            if (self.quality):
                path += "/" + self.quote(self.quality)
        if (self.format):
            path += "." + self.format
        return(path)

    def parseurl(self, url):
        """ Parse an IIIF API URL path
        "
        " Will parse a URL or URL path that accords with either the
        " parametrized or named profile API forms. Will throw an
        " exception on failure
        """
        # clear data first
        self.clear()
        # url must start with baseurl if set
        if (self.baseurl): 
            (path, num) = re.subn('^'+self.baseurl, '', url, 1)
            if (num != 1):
                raise(I3fError("URL does not match baseurl (server/prefix)"))
            url=path
        # Look for optional .fmt at end, must start with letter
        m = re.match( "(.+)\.([a-zA-Z]\w*)$", url)
        if (m):
            url = m.group(1)
            self.format = m.group(2)
        # Break up by path segments, count to decide format
        segs = string.split( url, '/', 5)
        if (len(segs) > 5):
            raise(I3fError("Too many path segments in URL"))
        elif (len(segs) >= 4):
            self.identifier = urllib.unquote(segs[0])
            self.region = urllib.unquote(segs[1])
            self.rotation = urllib.unquote(segs[2])
            self.size  = urllib.unquote(segs[3])
            if ( len(segs) == 5):
                self.quality = urllib.unquote(segs[4])
        elif (len(segs) == 2):
            self.identifier = urllib.unquote(segs[0])
            self.profile = urllib.unquote(segs[1])
        else:
            raise(I3fError("Bad number of path segments ("+len(segs)+") in URL"))
        return(self)

    def __str__(self):
        """ Utility method to pretty print this object in human form
        """
        s =  "baseurl    = " + str(self.baseurl) + "\n"
        s += "identifier = " + str(self.identifier) + "\n"
        s += "profile    = " + str(self.profile) + "\n"
        s += "region     = " + str(self.region) + "\n"
        s += "size       = " + str(self.size) + "\n"
        s += "rotation   = " + str(self.rotation) + "\n"
        s += "format     = " + str(self.format)
        return(s)
