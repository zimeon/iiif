""" Create and parse IIIF request URLs

This class is a thorough implementation of restrictions in the
IIIF specification. It does not add any implementation specific 
restrictions.
"""
import urllib
import re
import string

from error import IIIFError

class IIIFRequest:
    """ Implement IIIF request URL syntax
    
    There are two URL forms defined in section 2:
    http[s]://server/[prefix/]identifier/region/size/rotation/quality[.format]
    or
    http[s]://server/[prefix/]identifier/info.format

    The attribites of objects of this class follow the names here except that
    baseurl is used for "http[s]://server/[prefix/]". If baseurl is not set 
    then a relative URL will be created or parsed.
    """

    def __init__(self, **params):
        """Create Request object and optionally set any attributes via 
        named parameters

        Unless specified the baseurl will be set to nothing ("").
        """
        self.clear()
        self.region_full=False
        self.region_pct=False
        self.region_xywh=None # (x,y,w,h)
        self.size_wh=None     # (w,h)
        #
        self.baseurl = ''
        self.set(**params)

    def clear(self):
        """ Clear all data that might pertain to an individual iiif URL

        Does not change/reset the baseurl which might be useful in a
        sequence of calls.
        """
        self.identifier = None
        self.region = None
        self.size = None
        self.rotation = None
        self.quality = None
        self.format = None
        self.info = None
        # Other flags
        self.size_full = False
        self.size_pct = None
        self.size_bang = None
        self.rotation_deg = 0.0 

    def set(self, **params):
        # FIXME - maybe make this safe an allow only setting valid attributes
        self.__dict__.update(**params)

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
                region = "%d,%d,%d,%d" % (self.region_xywh[0],self.region_xywh[1],self.region_xywh[2],self.region_xywh[3]) #FIXME - how to get tiple from list
            else:
                region = "full"
            if self.size:
                size = self.size
            elif self.size_wh:
                size = "%d,%d" % (self.size_wh[0],self.size_wh[1])
            else:
                size = "full" 
            rotation = self.rotation if self.rotation else "0"
            quality = self.quality if self.quality else "native"
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
        # Look for optional .fmt at end, must start with letter. Note that we 
        # want to catch the case of a dot and no format (format='') which is
        # different from no dot (format=None)
        m = re.match( "(.+)\.([a-zA-Z]\w*)$", url)
        if (m):
            # There is a format string at end, chop off and store
            url = m.group(1)
            self.format = ( m.group(2) if (m.group(2) is not None) else '')
        # Break up by path segments, count to decide format
        segs = string.split( url, '/', 5)
        if (len(segs) > 5):
            raise(IIIFError(code=400,text="Too many path segments in URL (got %d: %s) in URL."%(len(segs),' | '.join(segs))))
        elif (len(segs) == 5):
            self.identifier = urllib.unquote(segs[0])
            self.region = urllib.unquote(segs[1])
            self.size  = urllib.unquote(segs[2])
            self.rotation = urllib.unquote(segs[3])
            self.quality = urllib.unquote(segs[4])
            self.info = False
        elif (len(segs) == 2):
            self.identifier = urllib.unquote(segs[0])
            if (urllib.unquote(segs[1]) != "info"):
                raise(IIIFError(code=400,text="Badly formed information request, must be info.json or info.xml"))
            if (self.format not in ("json","xml")):
                raise(IIIFError(code=400,text="Bad information request format, must be json or xml"))
            self.info = True
        else:
            raise(IIIFError(code=400,text="Bad number of path segments (%d: %s) in URL."%(len(segs),' | '.join(segs))))
        return(self)

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

    def parse_size(self):
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
            bang_match = re.match('!(.*)$',self.size)
            if (bang_match is not None):
                # Have "!w,h" form
                (mw,mh)=self._parse_w_comma_h(bang_match.group(1),'size')
                if (mw is None or mh is None):
                    raise IIIFError(code=400,parameter="size",
                                   text="Illegal size requested: both w,h must be specified in !w,h requests.")
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

    def _parse_w_comma_h(self,str,param):
        """ Utility to parse "w,h" "w," or ",h" values
        
        Returns (w,h) where w,h are either None or ineteger. Will
        throw a ValueError if there is a problem with one or both.
        """
        (wstr,hstr) = string.split(str, ',', 2)
        try:
            w = self._parse_non_negative_int(wstr,'w')
            h = self._parse_non_negative_int(hstr,'h')
        except ValueError as e:
            raise IIIFError(code=400,parameter=param,
                           text="Illegal parameter value (%s)." % str(e) )
        if (w is None and h is None):
            raise IIIFError(code=400,parameter=param,
                           text="Must specify at least one of w,h.")
        self.size_wh=(w,h)
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

    def parse_rotation(self):
        """ Check and interpret rotation

        Sets self.rotation_deg to a floating point number 0 <= angle < 360. Includes
        translation of 360 to 0.
        """
        if (self.rotation is None):
            self.rotation_deg=0.0
            return
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
            self.quality_val='native'
        elif (self.quality not in ['native','color','bitonal','grey']):
            raise IIIFError(code=400,parameter="quality",
                           text="The quality parameter must be 'native', 'color', 'bitonal' or 'grey', got '%s'."%(self.quality))
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
