"""IIIF Image Information Response.

Model for IIIF Image API 'Image Information Response'.
Default version is 2.1 but also supports 3.0, 2.0, 1.1 and 1.0.

Philisophy is to migrate this code forward with new versions
of the specification but to keep support for all published
versions.
"""

import sys
import json
import re


def _parse_string_or_array(json_data):
    # Parse either JSON single string or array into array.
    if (not isinstance(json_data, list)):
        json_data = [json_data]
    return json_data


def _parse_int_array(json_data):
    # Force simple array of interger values.
    return [int(x) for x in json_data]


def _parse_noop(json_data):
    # Format is already what we want.
    return json_data


def _parse_sizes(json_data):
    # Parse sizes in 2.0 and above.
    #
    # 3.0 spec: "A list of JSON objects with the height and width properties.
    # These sizes specify preferred values to be provided in the w,h syntax of
    # the size request parameter for scaled versions of the full image."
    if (not isinstance(json_data, list)):
        raise IIIFInfoError("The sizes property have a list value")
    for obj in json_data:
        if (not isinstance(obj, dict) or "width" not in obj or "height" not in obj):
            raise IIIFInfoError("Every entry in the sizes property list must have width and height")
    return json_data


def _parse_tile(json_data):
    # Parse data for a single tile specification.
    tile = {}
    tile['width'] = int(json_data['width'])
    if ('height' in json_data):
        tile['height'] = int(json_data['height'])
    tile['scaleFactors'] = _parse_int_array(json_data['scaleFactors'])
    return tile


def _parse_tiles(json_data):
    # Parse tiles array of tile specifications.
    #
    # Expect common case in 2.0 and above to map to 1.1 idea of
    # tile_width, tile_height and scale_factors. This is the case when
    # len()==1.
    tiles = []
    if (len(json_data) == 0):
        raise IIIFInfoError("Empty tiles array property not allowed.")
    for tile_spec in json_data:
        tiles.append(_parse_tile(tile_spec))
    return tiles


def _parse_service(json_data):
    return json_data


def _parse_profile_3_x(json_data):
    # 3.0 spec: "A string indicating the highest compliance level which is
    # fully supported by the service. The value must be one of "level0",
    # "level1", or "level2"."
    if (json_data not in ("level0", "level1", "level2")):
        raise IIIFInfoError("The value of the profile property must be a level string")
    return json_data


def _parse_profile_2_x(json_data):
    # 2.1 spec: "A list of profiles, indicated by either a URI or an
    # object describing the features supported. The first entry
    # in the list must be a compliance level URI."
    #
    # 2.0 spec: "An array of profiles, indicated by either a URI or
    # an object describing the features supported. The first entry in
    # the array must be a compliance level URI, as defined below."
    if (not isinstance(json_data, list)):
        raise IIIFInfoError("The profile property have a list value")
    if (not re.match(r'''http://iiif.io/api/image/2/level[012]\.json''', json_data[0])):
        raise IIIFInfoError("The first entry in the profile list must be a compliance level URI.")
    return json_data


def _parse_profile_1_1(json_data):
    # 1.1 & 1.0 spec: "URI indicating the compliance level supported.
    # Values as described in Section 8. Compliance Levels"
    if (not re.match(r'''http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level[012]''', json_data)):
        raise IIIFInfoError("The profile property value must be a compliance level URI.")
    return json_data


def _parse_profile_1_0(json_data):
    # 1.1 & 1.0 spec: "URI indicating the compliance level supported.
    # Values as described in Section 8. Compliance Levels"
    if (not re.match(r'''http://library.stanford.edu/iiif/image-api/compliance.html#level[012]''', json_data)):
        raise IIIFInfoError("The profile property value must be a compliance level URI.")
    return json_data


# Configuration information for API versions

CONF = {
    '1.0': {
        'params': [
            'id', 'protocol', 'width', 'height',
            'scale_factors', 'tile_width', 'tile_height',
            'extra_formats', 'extra_qualities', 'profile'
        ],
        'array_params': set([
            'scale_factors', 'extra_formats', 'extra_qualities'
        ]),
        'complex_params': {
            'profile': _parse_profile_1_0,
            'scale_factors': _parse_int_array,
            'extra_formats': _parse_noop,  # array of str
            'extra_qualities': _parse_noop  # array of str
        },
        'compliance_prefix': "http://library.stanford.edu/iiif/image-api/compliance.html#level",
        'compliance_suffix': "",
        'protocol': None,
        'required_params': ['id', 'width', 'height', 'profile'],
        'property_to_json': {
            'id': 'identifier',
            'extra_formats': 'formats',
            'extra_qualities': 'qualities'
        }
    },
    '1.1': {
        'params': [
            'id', 'protocol', 'width', 'height',
            'scale_factors', 'tile_width', 'tile_height',
            'extra_formats', 'extra_qualities', 'profile'
        ],
        'array_params': set([
            'scale_factors', 'extra_formats', 'extra_qualities'
        ]),
        'complex_params': {
            'profile': _parse_profile_1_1,
            'scale_factors': _parse_int_array,
            'extra_formats': _parse_noop,  # array of str
            'extra_qualities': _parse_noop  # array of str
        },
        'api_context': "http://library.stanford.edu/iiif/image-api/1.1/context.json",
        'compliance_prefix': "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level",
        'compliance_suffix': "",
        'protocol': None,
        'required_params': [
            'id', 'width', 'height', 'profile'
        ],
        'property_to_json': {
            'id': '@id',
            'extra_formats': 'formats',
            'extra_qualities': 'qualities'
        }
    },
    '2.0': {
        'params': [
            'id', 'protocol', 'width', 'height',
            'profile', 'sizes', 'tiles', 'service'
        ],
        # scale_factors isn't in API but used internally
        'array_params': set([
            'sizes', 'tiles', 'service', 'scale_factors', 'extra_formats',
            'extra_qualities', 'supports'
        ]),
        'complex_params': {
            'sizes': _parse_sizes,
            'tiles': _parse_tiles,
            'profile': _parse_profile_2_x,
            'service': _parse_service
        },
        'api_context': "http://iiif.io/api/image/2/context.json",
        'compliance_prefix': "http://iiif.io/api/image/2/level",
        'compliance_suffix': ".json",
        'protocol': "http://iiif.io/api/image",
        'required_params': [
            'id', 'protocol', 'width', 'height', 'profile'
        ],
        'property_to_json': {
            'id': '@id',
            'extra_formats': 'formats',
            'extra_qualities': 'qualities'
        }
    },
    '2.1': {
        'params': [
            'id', 'protocol', 'width', 'height',
            'profile', 'sizes', 'tiles', 'service',
            'attribution', 'logo', 'license'
        ],
        # scale_factors isn't in API but used internally
        'array_params': set([
            'sizes', 'tiles', 'service', 'scale_factors', 'extra_formats',
            'maxArea', 'maxHeight', 'maxWidth', 'extra_qualities', 'supports'
        ]),
        'complex_params': {
            'sizes': _parse_sizes,
            'tiles': _parse_tiles,
            'profile': _parse_profile_2_x,
            'service': _parse_service
        },
        'api_context': "http://iiif.io/api/image/2/context.json",
        'compliance_prefix': "http://iiif.io/api/image/2/level",
        'compliance_suffix': ".json",
        'protocol': "http://iiif.io/api/image",
        'required_params': [
            'id', 'protocol', 'width', 'height', 'profile'
        ],
        'property_to_json': {
            'id': '@id',
            'extra_formats': 'formats',
            'extra_qualities': 'qualities'
        }
    },
    '3.0': {
        'params': [
            'id', 'resource_type', 'protocol',
            'width', 'height', 'profile', 'sizes', 'tiles',
            'extra_formats', 'extra_qualities', 'extra_features',
            'service', 'attribution', 'logo', 'license'
        ],
        # scale_factors isn't in API but used internally
        'array_params': set([
            'sizes', 'tiles', 'service', 'scale_factors',
            'extra_formats', 'extra_qualities', 'extra_features',
            'maxArea', 'maxHeight', 'maxWidth'
        ]),
        'complex_params': {
            'sizes': _parse_sizes,
            'tiles': _parse_tiles,
            'profile': _parse_profile_3_x,
            'service': _parse_service
        },
        'api_context': "http://iiif.io/api/image/3/context.json",
        'compliance_prefix': "level",
        'compliance_suffix': "",
        'protocol': "http://iiif.io/api/image",
        'required_params': [
            'id', 'protocol', 'width', 'height', 'profile'
        ],
        'property_to_json': {
            'resource_type': 'type',
            'extra_formats': 'extraFormats',
            'extra_qualities': 'extraQualities',
            'extra_features': 'extraFeatures'
        },
        'fixed_values': {
            'resource_type': 'ImageService3'
        }
    }
}


class IIIFInfoError(Exception):
    """IIIFInfoError from IIIFInfo."""

    pass


class IIIFInfoContextError(IIIFInfoError):
    """IIIFInfoContextError for @context issues from IIIFInfo."""

    pass


class IIIFInfo(object):
    """IIIF Image Information Class."""

    def __init__(self, api_version='2.1', profile=None, level=1, conf=None,
                 server_and_prefix='',
                 identifier=None, width=None, height=None, tiles=None,
                 sizes=None, service=None, id=None,
                 # legacy params from 1.1
                 scale_factors=None, tile_width=None, tile_height=None,
                 # 1.1, 2.0, 2.1
                 formats=None, qualities=None,
                 # 2.0 and 2.1 only
                 supports=None,
                 # 2.1 only
                 attribution=None, logo=None, license=None,
                 # 3.0 only
                 extra_formats=None, extra_qualities=None,
                 extra_features=None,
                 ):
        """Initialize an IIIFInfo object.

        Parameters include:
        api_version -- defaults to 2.0 but may be set to 1.1
        profile -- usually not set but overrides handling via level
            (2.0 complex profile not supported except by explicitly
            passing in an array that matches JSON required)
        level -- default 1, generates compliance level for simple profile
        """
        # API version (used in level settings)
        if (api_version not in CONF):
            raise IIIFInfoError(
                "Unknown IIIF Image API version '%s', versions supported are ('%s')" %
                (api_version, sorted(CONF.keys())))
        self.api_version = api_version
        self.set_version_info()
        if (profile is not None):
            # Explicit profile setting overrides any level set
            # or default level
            self.profile = profile
        else:
            self.level = level
        # explicit settings
        self.server_and_prefix = server_and_prefix
        self.identifier = identifier
        self.width = width
        self.height = height
        self.tiles = tiles
        self.sizes = sizes
        self.service = service
        # legacy params for 1.0 and 1.1
        if (scale_factors is not None):
            self.scale_factors = scale_factors
        if (tile_width is not None):
            self.tile_width = tile_width
        if (tile_height is not None):
            self.tile_height = tile_height
        # 1.1+
        self.extra_formats = formats
        self.extra_qualities = qualities
        # 2.0+ only
        self.supports = supports
        # 2.1+ only
        self.attribution = attribution
        self.logo = logo
        self.license = license
        # 3.0 only
        if extra_formats:
            self.extra_formats = extra_formats
        if extra_qualities:
            self.extra_qualities = extra_qualities
        if extra_features:
            self.extra_features = extra_features
        # defaults from conf dict if provided
        if (conf):
            for option in conf:
                setattr(self, option, conf[option])
        if (id is not None):
            self.id = id

    @property
    def context(self):
        """Image API JSON-LD @context.

        Context taken from self.contexts, will return the last
        one if there are multiple, None if not set.
        """
        try:
            return self.contexts[-1]
        except:
            return None

    def add_context(self, context):
        """Add context to the set of contexts if not already present."""
        if context not in self.contexts:
            self.contexts.insert(0, context)

    @property
    def id(self):
        """id property based on server_and_prefix and identifier."""
        id = ''
        if (self.server_and_prefix is not None and
                self.server_and_prefix != ''):
            id += self.server_and_prefix + '/'
        if (self.identifier is not None):
            id += self.identifier
        return id

    @id.setter
    def id(self, value):
        """Split into server_and_prefix and identifier."""
        i = value.rfind('/')
        if (i > 0):
            self.server_and_prefix = value[:i]
            self.identifier = value[(i + 1):]
        elif (i == 0):
            self.server_and_prefix = ''
            self.identifier = value[(i + 1):]
        else:
            self.server_and_prefix = ''
            self.identifier = value

    def set_version_info(self, api_version=None):
        """Set version and load configuration for given api_version.

        Will use current value of self.api_version if a version number
        is not specified in the call. Will raise IIIFInfoError if an
        unknown API version is supplied.

        Sets a number of configuration properties from the content
        of CONF[api_version] which then control much of the rest of
        the behavior of this object.
        """
        if (api_version is None):
            api_version = self.api_version
        if (api_version not in CONF):
            raise IIIFInfoError("Unknown API version %s" % (api_version))
        # Load configuration for version
        self.params = CONF[api_version]['params']
        self.array_params = CONF[api_version]['array_params']
        self.complex_params = CONF[api_version]['complex_params']
        for a in ('api_context', 'compliance_prefix', 'compliance_suffix',
                  'protocol', 'required_params', 'property_to_json',
                  'fixed_values'):
            if (a in CONF[api_version]):
                self._setattr(a, CONF[api_version][a])
                if (a == 'api_context'):
                    self.contexts = [CONF[api_version][a]]
        # Set any fixed values
        if hasattr(self, 'fixed_values'):
            for p, v in self.fixed_values.items():
                self._setattr(p, v)

    def json_key(self, property):
        """JSON key for given object property name.

        If no mapping is specified then the JSON key is assumed to be
        the property name.
        """
        try:
            return self.property_to_json[property]
        except (AttributeError, KeyError):
            return property

    @property
    def compliance(self):
        """Compliance profile URI.

        In IIIF Image API v3.x the profile information is a JSON-LD
        aliased string representing the compliance level URI.

        In IIIF Image API v2.x the profile information is an array
        of values and objects, the first of which must be the
        compliance level URI.

        In IIIF Image API v1.x the profile information is
        just a single profile URI.
        """
        if self.api_version < '2.0':
            return self.profile
        elif self.api_version < '3.0':
            return self.profile[0]
        else:
            return self.profile

    @compliance.setter
    def compliance(self, value):
        """Set the compliance profile URI."""
        if (self.api_version < '2.0'):
            self.profile = value
        elif self.api_version < '3.0':
            try:
                self.profile[0] = value
            except AttributeError:
                # handle case where profile not initialized as array
                self.profile = [value]
        else:
            self.profile = value

    @property
    def level(self):
        """Extract level number from compliance profile URI.

        Returns integer level number or raises IIIFInfoError
        """
        m = re.match(
            self.compliance_prefix +
            r'(\d)' +
            self.compliance_suffix +
            r'$',
            self.compliance)
        if (m):
            return int(m.group(1))
        raise IIIFInfoError(
            "Bad compliance profile URI, failed to extract level number")

    @level.setter
    def level(self, value):
        """Build profile URI from level.

        Level should be an integer 0,1,2
        """
        self.compliance = self.compliance_prefix + \
            ("%d" % value) + self.compliance_suffix

    def _single_tile_getter(self, param):
        # Extract param from a single tileset defintion
        if (self.tiles is None or len(self.tiles) == 0):
            return None
        else:
            return self.tiles[0].get(param, None)

    def _single_tile_setter(self, param, value):
        # Set param for a single tileset defintion
        if (self.tiles is None or len(self.tiles) == 0):
            self.tiles = [{}]
        self.tiles[0][param] = value

    @property
    def scale_factors(self):
        """Access to scale_factors in 1.x.

        Also provides the scale factors in 2.0 and greated for
        only the first tile definition.
        """
        return self._single_tile_getter('scaleFactors')

    @scale_factors.setter
    def scale_factors(self, value):
        """Set scale_factors at version 1.1 and below.

        If used at 2.0+ this will create/edit the first entry
        in self.tiles. Will throw and error if it is used with more
        than on entry for self.tiles.
        """
        self._single_tile_setter('scaleFactors', value)

    @property
    def tile_width(self):
        """Access to tile_width in 1.x.

        Also provides the tile_width in 2.0 and greater for
        only the first tile definition.
        """
        return self._single_tile_getter('width')

    @tile_width.setter
    def tile_width(self, value):
        """Set tile_width at version 1.1 and below."""
        self._single_tile_setter('width', value)

    @property
    def tile_height(self):
        """Access to tile_height in 1.x.

        Also provides the tile_height in 2.0 and greaterfor
        only the first tile definition. If width is set but not
        height then return that instead.
        """
        h = self._single_tile_getter('height')
        if (h is None):
            return self._single_tile_getter('width')
        return h

    @tile_height.setter
    def tile_height(self, value):
        """Set tile_height at version 1.1 and below."""
        self._single_tile_setter('height', value)

    def add_service(self, service):
        """Add a service description.

        Handles transition from self.service=None, self.service=dict for a
        single service, and then self.service=[dict,dict,...] for multiple
        """
        if (self.service is None):
            self.service = service
        elif (isinstance(self.service, dict)):
            self.service = [self.service, service]
        else:
            self.service.append(service)

    def _setattr(self, param, value):
        # Setter handling array/scalar properties, and legacy.
        #
        # Also deals with legacy parameters that map to other
        # variables (but ugly!).
        if (param in self.array_params and
                isinstance(value, str)):
            # If we have an array then set directly, make list. Perhaps not
            # pythonic to do a type check for array here but want to avoid
            # accidentally iterating on chars in string etc..
            value = [value]
        setattr(self, param, value)

    def validate(self):
        """Validate this object as Image API data.

        Raise IIIFInfoError with helpful message if not valid.
        """
        errors = []
        for param in self.required_params:
            if (not hasattr(self, param) or getattr(self, param) is None):
                errors.append("missing %s parameter" % (param))
        if (len(errors) > 0):
            raise IIIFInfoError("Bad data for info.json: " + ", ".join(errors))
        return True

    def as_json(self, validate=True):
        """Return JSON serialization.

        Will raise IIIFInfoError if insufficient parameters are present to
        have a valid info.json response (unless validate is False).
        """
        if (validate):
            self.validate()
        json_dict = {}
        if (self.api_version > '1.0'):
            if (len(self.contexts) > 1):
                json_dict['@context'] = self.contexts
            else:
                json_dict['@context'] = self.context
        params_to_write = set(self.params)
        params_to_write.discard('id')
        if (self.identifier):
            if (self.api_version == '1.0'):
                json_dict['identifier'] = self.identifier  # local id
            else:
                json_dict[self.json_key('id')] = self.id  # URI
        params_to_write.discard('profile')
        if (self.compliance):
            if (self.api_version < '2.0'):
                json_dict['profile'] = self.compliance
            elif (self.api_version < '3.0'):
                # FIXME - need to support extra profile features
                json_dict['profile'] = [self.compliance]
                d = {}
                if (self.extra_formats is not None):
                    d['formats'] = self.extra_formats
                if (self.extra_qualities is not None):
                    d['qualities'] = self.extra_qualities
                if (self.supports is not None):
                    d['supports'] = self.extra_features
                if (len(d) > 0):
                    json_dict['profile'].append(d)
                params_to_write.discard('extra_formats')
                params_to_write.discard('extra_qualities')
                params_to_write.discard('extra_features')
            else:
                json_dict['profile'] = self.profile
        for param in params_to_write:
            if (hasattr(self, param) and
                    getattr(self, param) is not None):
                json_dict[self.json_key(param)] = getattr(self, param)
        return(json.dumps(json_dict, sort_keys=True, indent=2))

    def read_property(self, j, param):
        """Read one property param from JSON j."""
        key = self.json_key(param)
        if (key in j):
            value = j[key]
            if (param in self.complex_params):
                # use function ref in self.complex_params to parse
                value = self.complex_params[param](value)
            self._setattr(param, value)

    def read(self, fh, api_version=None):
        """Read info.json from file like object.

        Parameters:
        fh -- file like object supporting fh.read()
        api_version -- IIIF Image API version expected

        If api_version is set then the parsing will assume this API version,
        else the version will be determined from the incoming data. NOTE that
        the value of self.api_version is NOT used in this routine.

        If an api_version is specified and there is a @context specified then
        an IIIFInfoContextError will be raised unless these match. If no known
        @context is present and no api_version set then an IIIFInfoContextError
        will be raised.
        """
        # load and parse JSON
        j = json.load(fh)
        # must work out API version in order to know how to parse JSON
        # extract image API specific @context and API version
        if (api_version == '1.0'):
            # v1.0 did not have a @context so take the version passed in
            self.api_version = api_version
        else:
            try:
                self.contexts = _parse_string_or_array(j['@context'])
            except KeyError:
                # no @context and not 1.0
                if (api_version is None):
                    raise IIIFInfoContextError("No @context (and no default given)")
                self.api_version = api_version
            else:
                # determine API version from last context, pick highest
                # API version for a given context by searching highest
                # version first (i.e. get 2.1 not 2.0)
                api_version_read = None
                for v in sorted(CONF.keys(), reverse=True):
                    if (v > '1.0' and self.context == CONF[v]['api_context']):
                        api_version_read = v
                        break
                if api_version_read is None:
                    raise IIIFInfoContextError(
                        "Unknown @context, cannot determine API version (%s)" %
                        (self.context))
                elif api_version is None:
                    self.api_version = api_version_read
                elif api_version != api_version_read:
                    raise IIIFInfoContextError(
                        "Expected API version '%s' but got @context for API version '%s'" %
                        (api_version, api_version_read))
                if self.api_version < '3.0' and len(self.contexts) > 1:
                    raise IIIFInfoContextError("Multiple top-level @contexts not allowed in versions prior to v3.0")
        self.set_version_info()
        #
        # parse remaining JSON top-level keys
        for param in self.params:
            self.read_property(j, param)
        #
        # sanity check for id
        id_key = self.json_key('id')
        if id_key not in j:
            raise IIIFInfoError("Missing %s in info.json" % (id_key))
        return True

    @property
    def formats(self):
        """The pre 3.0 formats property tied to extra_formats."""
        return self.extra_formats

    @formats.setter
    def formats(self, value):
        """Set pre 3.0 formats by writing to alias extra_formats."""
        self.extra_formats = value

    @property
    def qualities(self):
        """The pre 3.0 qualities property tied to extra_qualities."""
        return self.extra_qualities

    @qualities.setter
    def qualities(self, value):
        """Set pre 3.0 qualitiess by writing to alias extra_qualities."""
        self.extra_qualities = value

    @property
    def supports(self):
        """The pre 3.0 supports property tied to extra_features."""
        return self.extra_features

    @supports.setter
    def supports(self, value):
        """Set pre 3.0 supports by writing to alias extra_features."""
        self.extra_features = value
