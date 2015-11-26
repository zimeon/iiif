"""Test code for iiif/info.py common code and IIIFInfoErrors"""
import unittest
import re #needed because no assertRegexpMatches in 2.6
try: #python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError: #python3
    import io
from iiif.info import IIIFInfo, IIIFInfoError, _parse_tiles

class TestAll(unittest.TestCase):

    def test01_bad_api_versions(self):
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='' )
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='0.9' )
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='1' )
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='2.9' )
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='3.0' )
        self.assertRaises( IIIFInfoError, IIIFInfo, api_version='goofy' )

    def test02_id(self):
        i = IIIFInfo()
        # setter
        i.id = ''
        self.assertEqual( i.server_and_prefix, '' )
        self.assertEqual( i.identifier, '' )
        i.id = 'a'
        self.assertEqual( i.server_and_prefix, '' )
        self.assertEqual( i.identifier, 'a' )
        i.id = 'a/b'
        self.assertEqual( i.server_and_prefix, 'a' )
        self.assertEqual( i.identifier, 'b' )
        i.id = 'a/b/c'
        self.assertEqual( i.server_and_prefix, 'a/b' )
        self.assertEqual( i.identifier, 'c' )
        i.id = 'a//b'
        self.assertEqual( i.server_and_prefix, 'a/' )
        self.assertEqual( i.identifier, 'b' )
        i.id = '/d'
        self.assertEqual( i.server_and_prefix, '' )
        self.assertEqual( i.identifier, 'd' )
        def xx(value): # FIXME - better way to test setter?
            i.id = value
        self.assertRaises( AttributeError, xx, None )
        self.assertRaises( AttributeError, xx, 123 )
        # property
        i.server_and_prefix = ''
        i.identifier = ''
        self.assertEqual( i.id, '' )
        i.identifier = 'abc'
        self.assertEqual( i.id, 'abc' )
        i.server_and_prefix = 'def'
        self.assertEqual( i.id, 'def/abc' )
        i.identifier = ''
        self.assertEqual( i.id, 'def/' )

    def test03_level(self):
        i = IIIFInfo()
        i.profile_prefix = 'prefix/'
        i.profile_suffix = '/suffix'
        # and good
        i.profile = 'prefix/2/suffix'
        self.assertEqual( i.level, 2 )        
        i.profile = 'prefix/3/suffix'
        self.assertEqual( i.level, 3 )   
        # and bad
        i.profile = ''
        self.assertRaises( IIIFInfoError, lambda: i.level ) # FIXME: how to avoid wrapping @property call in lamda?
        i.profile = 'prefix//suffix'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = 'prefix/22/suffix'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = 'prefix/junk/suffix'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = 'extra/prefix/2/suffix'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = '...2/suffix'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = 'prefix/2...'
        self.assertRaises( IIIFInfoError, lambda: i.level )
        i.profile = 'prefix/2/suffix/extra'
        self.assertRaises( IIIFInfoError, lambda: i.level )
    
    def test04_add_service(self):
        i = IIIFInfo()
        svc_a = {'a': '1'}
        svc_b = {'b': '2'}
        self.assertEqual( i.service, None )
        i.add_service(svc_a)
        self.assertEqual( i.service, svc_a )
        i.add_service(svc_b)
        self.assertEqual( i.service, [svc_a, svc_b] )
        i.add_service(svc_b)
        self.assertEqual( i.service, [svc_a, svc_b, svc_b] )

    def test05_set(self):
        i = IIIFInfo()
        i.array_params = set(['array'])
        # array param
        i.set('array','string')
        self.assertEqual( i.array, ['string'] )
        i.set('array',[1,2,3])
        self.assertEqual( i.array, [1,2,3] )
        # other param (trivial)
        i.set('other', 1234 )
        self.assertEqual( i.other, 1234 )

    def test06_validate(self):
        i = IIIFInfo()
        i.required_params = [ 'a', 'b', 'c' ]
        self.assertRaises( IIIFInfoError, i.validate )
        i.a = 1
        i.b = 2
        self.assertRaises( IIIFInfoError, i.validate )
        # check message
        try:
            i.validate()
        except IIIFInfoError as e:
            self.assertTrue( re.search( r'missing c parameter', str(e)) )
        i.d = 4
        self.assertRaises( IIIFInfoError, i.validate )
        i.c = 3
        self.assertTrue( i.validate() )

    def test07_read(self):
        i = IIIFInfo()
        fh = io.StringIO('{ "@id": "no_data" }')
        i.read(fh,api_version='2.0')
        self.assertEqual(i.api_version, '2.0')
        fh = io.StringIO('{ "@id": "no_data" }')
        self.assertRaises( IIIFInfoError, i.read, fh )
        # missing identifier cases
        fh = io.StringIO('{ }')
        self.assertRaises( IIIFInfoError, i.read, fh, api_version="1.0" )
        fh = io.StringIO('{ }')
        self.assertRaises( IIIFInfoError, i.read, fh, api_version="2.0" )
        # bad @context
        fh = io.StringIO('{ "@context": "oops" }')
        self.assertRaises( IIIFInfoError, i.read, fh )
        #
        fh = io.StringIO('{ "@context": "http://library.stanford.edu/iiif/image-api/1.1/context.json", "@id": "a" }')
        i.read( fh )
        self.assertEqual( i.api_version, '1.1')

    def test08_set_version_info(self):
        i = IIIFInfo()
        self.assertRaises( IIIFInfoError, i.set_version_info, api_version='9.9' )

    def test09_parse_tiles(self):
        i = IIIFInfo()
        jd = [ { 'width': 512, 'scaleFactors': [1,2,4] } ]
        self.assertEqual( _parse_tiles(i,jd), jd )
        self.assertEqual( i.tile_width, 512 )
        self.assertEqual( i.tile_height, 512 )
        self.assertEqual( i.scale_factors, [1,2,4] )
        i = IIIFInfo()
        jd = [ { 'width': 256, 'height': 200, 'scaleFactors': [1] } ]
        self.assertEqual( _parse_tiles(i,jd), jd )
        self.assertEqual( i.tile_width, 256 )
        self.assertEqual( i.tile_height, 200 )
        self.assertEqual( i.scale_factors, [1] )
        # error case - empty tiles
        i = IIIFInfo()
        jd = [ ]
        self.assertRaises( IIIFInfoError, _parse_tiles, i,jd )
        # unsupported case of multiple tile sizes
        i = IIIFInfo()
        jd = [ { 'width': 256, 'scaleFactors': [1] },
               { 'width': 512, 'scaleFactors': [1] } ]
        self.assertRaises( IIIFInfoError, _parse_tiles, i,jd )


