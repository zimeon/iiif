""" Create and parse IIIF request URLs

This class is a thorough implementation of restrictions in the
IIIF specification. It does not add any implementation specific 
restrictions.
"""
import urllib
import re
import string

from error import IIIFError

class IIIFRequestBaseURI(Exception):
    """ Subclass of Exception to indicate request for base URI """
    pass

class IIIFRequest(object):
    """ Implement IIIF request URL syntax
    
    There are two URL forms defined in section 2:
    http[s]://server/[prefix/]identifier/region/size/rotation/quality[.format]
    or
    http[s]://server/[prefix/]identifier/info.format

    We also detect and throw a special IIIFRequestBaseURI exception then
    the naked base URI is requested:
    http[s]://server/[prefix/]identifier(/?)

    The attribites of objects of this class follow the names here except that
    baseurl is used for "http[s]://server/[prefix/]". If baseurl is not set 
    then a relative URL will be created or parsed.
    """

    def __init__(self, api_version='2.0', **params):
        """Create Request object and optionally set any attributes via 
        named parameters.

        Current API version assumed ('2.0') if not specified. If another API
        version is to be used then this should be set on creation via the
        api_version parameter.
 
        Unless specified the baseurl will be set to nothing ("").
        """
        self.baseurl = ''
        self.api_version = api_version
        self.clear()
        self.set(**params)

    def clear(self):
        """ Clear all data that might pertain to an individual IIIF URL

        Does not change/reset the baseurl or API version which might be 
        useful in a sequence of calls.
        """
        # API parameters
        self.identifier = None
        self.region = None
        self.size = None
        self.rotation = None
        self.quality = None
        self.format = None
        self.info = None
        # Derived data and flags
        self.region_full = False
        self.region_pct = False
        self.region_xywh = None # (x,y,w,h)
        self.size_full = False
        self.size_pct = None
        self.size_bang = None
        self.size_wh = None     # (w,h)
        self.rotation_mirror = False
        self.rotation_deg = 0.0 

    @property
    def api_version(self):
        """ Get api_version value """
        return self._api_version

    @api_version.setter
    def api_version(self,v):
        """ Set the api_version and associated configurations """
        self._api_version=v
        if (self._api_version>='2.0'):
            self.default_quality = 'default'
            self.allowed_qualities = ['default','color','bitonal','gray']
        else: # versions 1.0 and 1.1
            self.default_quality = 'native'
            self.allowed_qualities = ['native','color','bitonal','grey']

    def set(self, **params):
        """ Set one of the allowed request parameters

        Will silently ignore any unknown parameters.
        """
        for k in ('identifier','region','size','rotation','quality','format','info'):
            if (k in params):
                setattr(self, k, params[k])

    def quote(self, path_segment):
        """ Quote parameters in IIIF URLs

        Quote by percent-encoding "%" and gen-delims of RFC3986 exept colon
        
        http://tools.ietf.org/html/rfc3986#section-2.3
        gen-delims  = ":" / "/" / "?" / "#" / "[" / "]" / "@"
         
        to-encode = "%" / "/" / "?" / "#" / "[" / "]" / "@"
        """
        return( urllib.quote(path_segment,"-._~!$&'()*+,;=:") ) #FIXME - quotes too much

    def url(self, **params):
        """ Build a URL path according to the IIIF API parameterized or 
            info form

        The parameterized form is assumed unless a the info parameter is 
        specified.
        """
        self.set(**params)
        path = self.baseurl +\
            self.quote(self.identifier) + "/"
        if (self.info):
            # info request
            path += "info"
            format = self.format if self.format else "json"
        else:
            # set defaults if not given
            if self.region:
                region = self.region
            elif self.region_xywh:
                region = "%d,%d,%d,%d" % tuple(self.region_xywh)
            else:
                region = "full"
            if self.size:
                size = self.size
            elif self.size_wh:
                size = "%d,%d" % (self.size_wh[0],self.size_wh[1])
            else:
                size = "full" 
            rotation = self.rotation if self.rotation else "0"
            quality = self.quality if self.quality else self.default_quality
            # parameterized form
            path += self.quote(region) + "/" +\
                    self.quote(size) + "/" +\
                    self.quote(rotation) + "/" +\
                    self.quote(quality)
            format = self.format
        if (format):
            path += "." + format
        return(path)

    def parse_url(self, url):
        """ Parse an IIIF API URL path and each component
        
        Will parse a URL or URL path that accords with either the
        parametrized or info request forms. Will raise an
        IIIFError on failure. A wrapper for the split_url()
        and parse_parameters() methods.
        """
        self.split_url(url)
        if (not self.info):
            self.parse_parameters()
        return(self)

    def split_url(self,url):
        """ Perform the initial parsing of an IIIF API URL path into components

        Will parse a URL or URL path that accords with either the
        parametrized or info API forms. Will raise an IIIFError on 
        failure.
        """
        # clear data first
        self.clear()
        # url must start with baseurl if set
        if (self.baseurl): 
            (path, num) = re.subn('^'+self.baseurl, '', url, 1)
            if (num != 1):
                raise(IIIFError("URL does not match baseurl (server/prefix)."))
            url=path
        # Break up by path segments, count to decide format
        segs = string.split( url, '/', 5)
        if (len(segs) > 5):
            raise(IIIFError(code=404,text="Too many path segments in URL (got %d: %s) in URL."%(len(segs),' | '.join(segs))))
        elif (len(segs) == 5):
            self.identifier = urllib.unquote(segs[0])
            self.region = urllib.unquote(segs[1])
            self.size  = urllib.unquote(segs[2])
            self.rotation = urllib.unquote(segs[3])
            self.quality = self.strip_format(urllib.unquote(segs[4]))
            self.info = False
        elif (len(segs) == 2):
            self.identifier = urllib.unquote(segs[0])
            info_name = self.strip_format(urllib.unquote(segs[1]))
            if (info_name != "info"):
                raise(IIIFError(code=400,text="Badly formed information request, must be info.json or info.xml"))
            if (self.api_version=='1.0'):
                if (self.format not in ['json','xml']):
                    raise(IIIFError(code=400,text="Bad information request format, must be json or xml"))
            elif (self.format!='json'):
                raise(IIIFError(code=400,text="Bad information request format, must be json"))
            self.info = True
        elif (len(segs) == 1):
            self.identifier = urllib.unquote(segs[0])
            raise(IIIFRequestBaseURI())
        else:
            raise(IIIFError(code=400,text="Bad number of path segments (%d: %s) in URL."%(len(segs),' | '.join(segs))))
        return(self)

    def strip_format(self,str_and_format):
        """ Look for optional .fmt at end

        The format must start with letter. Note that we want to catch 
        the case of a dot and no format (format='') which is different 
        from no dot (format=None)
        
        Sets self.format as side effect, returns possibly modified string
        """
        m = re.match( "(.+)\.([a-zA-Z]\w*)$", str_and_format)
        if (m):
            # There is a format string at end, chop off and store
            str_and_format = m.group(1)
            self.format = ( m.group(2) if (m.group(2) is not None) else '')
        return(str_and_format)

    def parse_parameters(self):
        """ Parse the parameters of a parameterized request

        Will throw an IIIFError on failure, set attributes on success. Care is 
        take not to change any of the artibutes which store path components, 
        all parsed values are stored in new attributes.
        """
        self.parse_region()
        self.parse_size()
        self.parse_rotation()
        self.parse_quality()
        self.parse_format()

    def parse_region(self):
        """ Parse the region component of the path

        /full/ -> self.region_full = True (test this first)
        /x,y,w,h/ -> self.region_xywh = (x,y,w,h)
        /pct:x,y,w,h/ -> self.region_xywh and self.region_pct = True

        Will throw errors if the paremeters are illegal according to the
        specification but does not know about and thus cannot do any tests
        against any image being manipulated.
        """
        self.region_full=False
        self.region_pct=False
        if (self.region is None or self.region == 'full'):
            self.region_full=True
            return
        xywh=self.region
        pct_match = re.match('pct:(.*)$',self.region)
        if (pct_match):
            xywh=pct_match.group(1)
            self.region_pct=True
        # Now whether this was pct: or now, we expect 4 values...
        str_values = string.split(xywh, ',', 5)
        if (len(str_values) != 4):
            raise IIIFError(code=400,parameter="region",
                            text="Bad number of values in region specification, must be x,y,w,h but got %d value(s) from '%s'"%(len(str_values),xywh))
        values=[]
        for str_value in str_values:
            # Must be either integer (not pct) or interger/float (pct)
            if (pct_match):
                try:
                    # This is rather more permissive that the iiif spec
                    value=float(str_value)
                except ValueError:
                    raise IIIFError(code=400,parameter="region",
                                   text="Bad floating point value for percentage in region (%s)."%str_value)
                if (value>100.0):
                    raise IIIFError(code=400,parameter="region",
                                    text="Percentage over value over 100.0 in region (%s)."%str_value)
            else:
                try:
                    value=int(str_value)
                except ValueError:
                    raise IIIFError(code=400,parameter="region",
                                    text="Bad integer value in region (%s)."%str_value)
            if (value<0):
                raise IIIFError(code=400,parameter="region",
                                text="Negative values not allowed in region (%s)."%str_value)
            values.append(value)
        # Zero size region is w or h are zero (careful that they may be float)
        if (values[2]==0.0 or values[3]==0.0):
            raise IIIFError(code=400,parameter="region",
                            text="Zero size region specified (%s))."%xywh)
        self.region_xywh=values

    def parse_size(self,size=None):
        """Parse the size component of the path

        /full/ -> self.size_full = True
        /w,/ -> self.size_wh = (w,None)
        /,h/ -> self.size_wh = (None,h)
        /w,h/ -> self.size_wh = (w,h)
        /pct:p/ -> self.size_pct = p
        /!w,h/ -> self.size_wh = (w,h), self.size_bang = True

        Expected use:
          (w,h) = iiif.size_to_apply(region_w,region_h)
          if (q is None):
              # full image
          else:
              # scale to w by h
        Returns (None,None) if no scaling is required.
        """
        if (size is not None):
            self.size = size
        self.size_pct=None
        self.size_bang=False
        self.size_full=False
        self.size_wh=(None,None)
        if (self.size is None or self.size=='full'):
            self.size_full=True
            return
        pct_match = re.match('pct:(.*)$',self.size)
        if (pct_match is not None):
            pct_str=pct_match.group(1)
            try:
                self.size_pct=float(pct_str)
            except ValueError:
                raise IIIFError(code=400,parameter="size",
                                text="Percentage size value must be a number, got '%s'."%(pct_str))
# FIXME - current spec places no upper limit on size
#            if (self.size_pct<0.0 or self.size_pct>100.0):
#                raise IIIFError(code=400,parameter="size",
#                               text="Illegal percentage size, must be 0 <= pct <= 100.")
            if (self.size_pct<0.0):
                raise IIIFError(code=400,parameter="size",
                                text="Base size percentage, must be > 0.0, got %f."%(self.size_pct))
        else:
            if (self.size[0]=='!'):
                # Have "!w,h" form
                size_no_bang=self.size[1:]
                (mw,mh)=self._parse_w_comma_h(size_no_bang,'size')
                if (mw is None or mh is None):
                    raise IIIFError(code=400,parameter="size",
                                    text="Illegal size requested: both w,h must be specified in !w,h requests.")
                self.size_wh=(mw,mh)
                self.size_bang=True
            else:
                # Must now be "w,h", "w," or ",h"
                self.size_wh=self._parse_w_comma_h(self.size,'size')
            # Sanity check w,h
            (w,h) = self.size_wh
            if ( ( w is not None and w<=0) or 
                 ( h is not None and h<=0) ):
                raise IIIFError(code=400,parameter='size',
                                text="Size parameters request zero size result image.")

    def _parse_w_comma_h(self,whstr,param):
        """ Utility to parse "w,h" "w," or ",h" values
        
        Returns (w,h) where w,h are either None or ineteger. Will
        throw a ValueError if there is a problem with one or both.
        """
        try:
            (wstr,hstr) = string.split(whstr, ',', 2)
            w = self._parse_non_negative_int(wstr,'w')
            h = self._parse_non_negative_int(hstr,'h')
        except ValueError as e:
            raise IIIFError(code=400,parameter=param,
                            text="Illegal %s value (%s)." % (param,str(e)) )
        if (w is None and h is None):
            raise IIIFError(code=400,parameter=param,
                            text="Must specify at least one of w,h for %s." % (param))
        return(w,h)

    def _parse_non_negative_int(self,istr,name):
        """ Parse integer from string (istr)

        The (name) parameter is used just for IIIFError message generation
        to indicate what the error is in.
        """
        if (istr == ''):
            return(None)
        try:
            i = int(istr)
        except ValueError:
            raise ValueError("Failed to extract integer value for %s" % (name))
        if (i<0):
            raise ValueError("Illegal negative value for %s" % (name))
        return(i)

    def parse_rotation(self, rotation=None):
        """ Check and interpret rotation

        Uses value of self.rotation at starting point unless rotation parameter
        is specified in the call. Sets self.rotation_deg to a floating point 
        number 0 <= angle < 360. Includes translation of 360 to 0. If there is 
        a prefix bang (!) then self.rotation_mirror will be set True, otherwise
        it will be False.
        """
        if (rotation is not None):
            self.rotation = rotation
        self.rotation_deg=0.0
        self.rotation_mirror=False
        if (self.rotation is None):
            return
        # Look for ! prefix first
        if (self.rotation[0]=='!'):
            self.rotation_mirror=True
            self.rotation=self.rotation[1:]
        # Interpret value now
        try:
            self.rotation_deg=float(self.rotation)
        except ValueError:
            raise IIIFError(code=400,parameter="rotation",
                            text="Bad rotation value, must be a number, got '%s'."%(self.rotation))
        if (self.rotation_deg<0.0 or self.rotation_deg>360.0):
            raise IIIFError(code=400,parameter="rotation",
                            text="Illegal rotation value, must be 0 <= rotation <= 360, got %f."%(self.rotation_deg))
        elif (self.rotation_deg==360.0):
            # The spec admits 360 as valid, but change to 0
            self.rotation_deg=0.0

    def parse_quality(self):
        """ Check quality paramater

        Sets self.quality_val based on simple substitution of 'native' for 
        default. Checks for the three valid values else throws and IIIFError.
        """
        if (self.quality is None):
            self.quality_val=self.default_quality
        elif (self.quality not in self.allowed_qualities):
            raise IIIFError(code=400,parameter="quality",
                            text="The quality parameter must be '%s', got '%s'."%("', '".join(self.allowed_qualities),self.quality))
        else:
            self.quality_val=self.quality

    def parse_format(self):
        """ Check format parameter

        FIXME - do something...
        """
        pass

    def __str__(self):
        """ Pretty print this object in human readable form
        
        Distinguishes parametrerized and info requests to
        show only appropriate parameters in each case.
        """
        s =  "baseurl=" + str(self.baseurl) + " "
        s += "identifier=" + str(self.identifier) + " "
        if (self.info):
            s += "INFO request ";
            s += "format=" + str(self.format) + " "
        else:
            s += "region=" + str(self.region) + " "
            s += "size=" + str(self.size) + " "
            s += "rotation=" + str(self.rotation) + " "
            s += "quality=" + str(self.quality) + " "
            s += "format=" + str(self.format)
        return(s)
