"""Test code for iiif/info.py common code and IIIFInfoErrors."""
import unittest
try:  # python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io
from iiif.info import IIIFInfo, IIIFInfoError, _parse_tiles


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_bad_api_versions(self):
        """Test handling of bad API versions."""
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='')
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='0.9')
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='1')
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='2.9')
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='4.0')
        self.assertRaises(IIIFInfoError, IIIFInfo, api_version='goofy')

    def test02_id(self):
        """Test identifier handling."""
        i = IIIFInfo()
        # setter
        i.id = ''
        self.assertEqual(i.server_and_prefix, '')
        self.assertEqual(i.identifier, '')
        i.id = 'a'
        self.assertEqual(i.server_and_prefix, '')
        self.assertEqual(i.identifier, 'a')
        i.id = 'a/b'
        self.assertEqual(i.server_and_prefix, 'a')
        self.assertEqual(i.identifier, 'b')
        i.id = 'a/b/c'
        self.assertEqual(i.server_and_prefix, 'a/b')
        self.assertEqual(i.identifier, 'c')
        i.id = 'a//b'
        self.assertEqual(i.server_and_prefix, 'a/')
        self.assertEqual(i.identifier, 'b')
        i.id = '/d'
        self.assertEqual(i.server_and_prefix, '')
        self.assertEqual(i.identifier, 'd')
        # id setter
        self.assertRaises(AttributeError, setattr, i, 'id', None)
        self.assertRaises(AttributeError, setattr, i, 'id', 123)
        # property
        i.server_and_prefix = ''
        i.identifier = ''
        self.assertEqual(i.id, '')
        i.identifier = 'abc'
        self.assertEqual(i.id, 'abc')
        i.server_and_prefix = 'def'
        self.assertEqual(i.id, 'def/abc')
        i.identifier = ''
        self.assertEqual(i.id, 'def/')

    def test03_set_version_info(self):
        """Test setting of version information."""
        i = IIIFInfo()
        self.assertRaises(IIIFInfoError, i.set_version_info, api_version='9.9')

    def test04_json_key(self):
        """Test json_key()."""
        i = IIIFInfo()
        self.assertEqual(i.json_key(None), None)
        self.assertEqual(i.json_key(''), '')
        self.assertEqual(i.json_key('abc'), 'abc')
        i.set_version_info('3.0')
        self.assertEqual(i.json_key(None), None)
        self.assertEqual(i.json_key(''), '')
        self.assertEqual(i.json_key('abc'), 'abc')
        self.assertEqual(i.json_key('identifier'), 'id')

    def test03_level(self):
        """Test level handling."""
        i = IIIFInfo()
        i.compliance_prefix = 'prefix/'
        i.compliance_suffix = '/suffix'
        # and good
        i.compliance = 'prefix/2/suffix'
        self.assertEqual(i.level, 2)
        i.compliance = 'prefix/3/suffix'
        self.assertEqual(i.level, 3)
        # and bad
        i.compliance = ''
        # FIXME: how to avoid wrapping @property call in lamda?
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'prefix//suffix'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'prefix/22/suffix'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'prefix/junk/suffix'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'extra/prefix/2/suffix'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = '...2/suffix'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'prefix/2...'
        self.assertRaises(IIIFInfoError, lambda: i.level)
        i.compliance = 'prefix/2/suffix/extra'
        self.assertRaises(IIIFInfoError, lambda: i.level)

    def test04_add_service(self):
        """Test addition of services."""
        i = IIIFInfo()
        svc_a = {'a': '1'}
        svc_b = {'b': '2'}
        self.assertEqual(i.service, None)
        i.add_service(svc_a)
        self.assertEqual(i.service, svc_a)
        i.add_service(svc_b)
        self.assertEqual(i.service, [svc_a, svc_b])
        i.add_service(svc_b)
        self.assertEqual(i.service, [svc_a, svc_b, svc_b])

    def test05_set(self):
        """Test custom setter."""
        i = IIIFInfo()
        i.array_params = set(['array'])
        # array param
        i._setattr('array', 'string')
        self.assertEqual(i.array, ['string'])
        i._setattr('array', [1, 2, 3])
        self.assertEqual(i.array, [1, 2, 3])
        # other param (trivial)
        i._setattr('other', 1234)
        self.assertEqual(i.other, 1234)

    def test06_validate(self):
        """Test validate method."""
        i = IIIFInfo()
        i.required_params = ['a', 'b', 'c']
        self.assertRaises(IIIFInfoError, i.validate)
        i.a = 1
        i.b = 2
        self.assertRaises(IIIFInfoError, i.validate)
        # check message
        try:
            i.validate()
        except IIIFInfoError as e:
            self.assertRegexpMatches(str(e), r'missing c parameter')
        i.d = 4
        self.assertRaises(IIIFInfoError, i.validate)
        i.c = 3
        self.assertTrue(i.validate())

    def test07_read(self):
        """Read test."""
        i = IIIFInfo()
        fh = io.StringIO('{ "@id": "no_data" }')
        i.read(fh, api_version='2.0')
        self.assertEqual(i.api_version, '2.0')
        fh = io.StringIO('{ "@id": "no_data" }')
        self.assertRaises(IIIFInfoError, i.read, fh)
        # missing identifier cases
        fh = io.StringIO('{ }')
        self.assertRaises(IIIFInfoError, i.read, fh, api_version="1.0")
        fh = io.StringIO('{ }')
        self.assertRaises(IIIFInfoError, i.read, fh, api_version="2.0")
        # bad @context
        fh = io.StringIO('{ "@context": "oops" }')
        self.assertRaises(IIIFInfoError, i.read, fh)
        # minimal 1.1 -- @context and @id
        fh = io.StringIO(
            '{ "@context": "http://library.stanford.edu/iiif/image-api/1.1/context.json", "@id": "a" }')
        i.read(fh)
        self.assertEqual(i.api_version, '1.1')

    def test09_parse_tiles(self):
        """Test _parse_tiles function."""
        jd = [{'width': 512, 'scaleFactors': [1, 2, 4]}]
        self.assertEqual(_parse_tiles(jd), jd)
        jd = [{'width': 256, 'height': 200, 'scaleFactors': [1]}]
        self.assertEqual(_parse_tiles(jd), jd)
        # error case - empty tiles
        jd = []
        self.assertRaises(IIIFInfoError, _parse_tiles, jd)

    def test20_scale_factors(self):
        """Test getter/setter for scale_factors property."""
        i = IIIFInfo(api_version='1.1')
        self.assertEqual(i.scale_factors, None)
        i.scale_factors = [1, 2]
        self.assertEqual(i.scale_factors, [1, 2])
        i.scale_factors = [7, 8]
        self.assertEqual(i.scale_factors, [7, 8])

    def test21_tile_width_tile_height(self):
        """Test getters/setters for tile_width and tile_height."""
        i = IIIFInfo(api_version='1.1')
        self.assertEqual(i.tile_width, None)
        i.tile_width = 123
        self.assertEqual(i.tile_width, 123)
        self.assertEqual(i.tile_height, 123)
        i.tile_width = 124
        self.assertEqual(i.tile_width, 124)
        self.assertEqual(i.tile_height, 124)
        # once height it set, it won't inherit from future width setting
        i.tile_height = 255
        self.assertEqual(i.tile_width, 124)
        self.assertEqual(i.tile_height, 255)
        i.tile_width = 345
        self.assertEqual(i.tile_width, 345)
        self.assertEqual(i.tile_height, 255)
