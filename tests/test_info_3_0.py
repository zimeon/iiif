"""Test code for iiif/info.py for Image API v3.0."""
import unittest
from .testlib.assert_json_equal_mixin import AssertJSONEqual
import json
import os.path
from iiif.info import IIIFInfo, IIIFInfoError, IIIFInfoContextError


class TestAll(unittest.TestCase, AssertJSONEqual):
    """Tests."""

    def open_testdata(self, filename):
        """Open test data file."""
        return open(os.path.join('tests/testdata/info_json_3_0', filename))

    def test01_minmal(self):
        """Trivial JSON test."""
        # ?? should this empty case raise and error instead?
        ir = IIIFInfo(identifier="https://example.com/i1", api_version='3.0')
        self.assertJSONEqual(ir.as_json(validate=False),
                             '{\n  "@context": "http://iiif.io/api/image/3/context.json", \n  "id": "https://example.com/i1", \n  "profile": "level1", \n  "protocol": "http://iiif.io/api/image", "type": "ImageService3"\n}')
        ir.width = 100
        ir.height = 200
        self.assertJSONEqual(ir.as_json(),
                             '{\n  "@context": "http://iiif.io/api/image/3/context.json", \n  "height": 200, \n  "id": "https://example.com/i1", \n  "profile": "level1", \n  "protocol": "http://iiif.io/api/image",  \n"type": "ImageService3",\n  "width": 100\n}')

    def test04_conf(self):
        """Tile parameter configuration."""
        conf = {'tiles': [{'width': 999, 'scaleFactors': [9, 8, 7]}]}
        i = IIIFInfo(api_version='3.0', conf=conf)
        self.assertEqual(i.tiles[0]['width'], 999)
        self.assertEqual(i.tiles[0]['scaleFactors'], [9, 8, 7])
        # 1.1 style values
        self.assertEqual(i.tile_width, 999)
        self.assertEqual(i.scale_factors, [9, 8, 7])

    def test05_level_and_profile(self):
        """Test level and profile setting."""
        i = IIIFInfo(api_version='3.0')
        i.level = 0
        self.assertEqual(i.level, 0)
        self.assertEqual(i.compliance, "level0")
        i.level = 2
        self.assertEqual(i.level, 2)
        self.assertEqual(i.compliance, "level2")
        # Set via compliance
        i.compliance = "level1"
        self.assertEqual(i.level, 1)
        # Set via profile
        i.profile = "level2"
        self.assertEqual(i.level, 2)
        # Set new via compliance
        i = IIIFInfo(api_version='3.0')
        i.compliance = "level1"
        self.assertEqual(i.level, 1)

    def test06_validate(self):
        """Test validate method."""
        i = IIIFInfo(api_version='3.0')
        self.assertRaises(IIIFInfoError, i.validate)
        i = IIIFInfo(identifier='a')
        self.assertRaises(IIIFInfoError, i.validate)
        i = IIIFInfo(identifier='a', width=1, height=2)
        self.assertTrue(i.validate())

    def test10_read_examples_from_spec(self):
        """Test reading of examples from spec."""
        # Section 5.2, max dimensions
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_2.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.resource_type, "ImageService3")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        # Section 5.3, sizes
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_3.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.resource_type, "ImageService3")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.sizes, [{"width": 150, "height": 100},
                                   {"width": 600, "height": 400},
                                   {"width": 3000, "height": 2000}])
        self.assertEqual(i.profile, "level2")
        self.assertEqual(i.compliance, "level2")
        # Section 5.4, tiles
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_4.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.resource_type, "ImageService3")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.tiles, [{"width": 512,
                                    "scaleFactors": [1, 2, 4, 8, 16]}])
        self.assertEqual(i.profile, "level2")
        self.assertEqual(i.compliance, "level2")
        # and 1.1 style tile properties
        self.assertEqual(i.tile_width, 512)
        self.assertEqual(i.tile_height, 512)
        self.assertEqual(i.scale_factors, [1, 2, 4, 8, 16])
        # Section 5.5, rights etc.
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_5.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.profile, "level2")
        self.assertEqual(i.attribution, "Provided by Example Organization")
        self.assertEqual(i.logo, "https://example.org/images/logo.png")
        self.assertEqual(i.license, "http://rightsstatements.org/vocab/InC-EDU/1.0/")
        # Section 5.7, simple service
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_7.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.profile, "level2")
        self.assertEqual(i.compliance, "level2")
        self.assertEqual(i.service, [{
            "@id": "https://example.org/auth/login.html",
            "@type": "AuthCookieService1",
            "profile": "http://iiif.io/api/auth/1/login"
        }])
        # Section 5.8, full example
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_from_spec_section_5_8.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.sizes, [{"width": 150, "height": 100},
                                   {"width": 600, "height": 400},
                                   {"width": 3000, "height": 2000}])

    def test11_read_example_with_extra(self):
        """Test read of exampe with extra info."""
        i = IIIFInfo(api_version='3.0')
        fh = self.open_testdata('info_with_extra.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/3/context.json")
        self.assertEqual(i.id,
                         "https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(
            i.tiles, [{"width": 512, "scaleFactors": [1, 2, 4, 8, 16]}])
        # and should have 1.1-like params too
        self.assertEqual(i.tile_width, 512)
        self.assertEqual(i.scale_factors, [1, 2, 4, 8, 16])
        self.assertEqual(i.compliance, "level2")

    def test12_read_bad_context(self):
        """Test bad/unknown context."""
        for ctx_file in ['info_bad_context1.json',
                         'info_bad_context2.json',
                         'info_bad_context3.json']:
            i = IIIFInfo(api_version='3.0')
            fh = self.open_testdata(ctx_file)
            self.assertRaises(IIIFInfoContextError, i.read, fh)

    def test13_read_good_context(self):
        """Test good context."""
        for ctx_file in ['info_good_context1.json',
                         'info_good_context2.json',
                         'info_good_context3.json']:
            i = IIIFInfo()
            i.read(self.open_testdata(ctx_file))
            self.assertEqual(i.api_version, '3.0')

    def test20_write_full_example_in_spec(self):
        """Create example info.json in spec."""
        i = IIIFInfo(
            api_version='3.0',
            id="https://example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C",
            # "protocol" : "http://iiif.io/api/image",
            width=6000,
            height=4000,
            sizes=[
                {"width": 150, "height": 100},
                {"width": 600, "height": 400},
                {"width": 3000, "height": 2000}],
            tiles=[
                {"width": 512, "scaleFactors": [1, 2, 4]},
                {"width": 1024, "height": 2048, "scaleFactors": [8, 16]}],
            attribution=[
                {"@value": "<span>Provided by Example Organization</span>",
                 "@language": "en"},
                {"@value": "<span>Darparwyd gan Enghraifft Sefydliad</span>",
                 "@language": "cy"}],
            logo={"id": "https://example.org/image-service/logo/square/200,200/0/default.png",
                  "service":
                  [{"id": "https://example.org/image-service/logo",
                    "profile": "level2",
                    'type': 'ImageService3'}]},
            license=[
                "https://example.org/rights/license1.html",
                "http://rightsstatements.org/vocab/InC-EDU/1.0/"],
            profile="level1",
            extra_formats=["gif", "pdf"],
            extra_qualities=["color", "gray"],
            extra_features=["canonicalLinkHeader", "rotationArbitrary",
                            "profileLinkHeader"],
            service=[{'id': 'http://example.org/fix/me'}]
        )
        i.add_context("http://example.org/extension/context1.json")
        reparsed_json = json.loads(i.as_json())
        example_json = json.load(self.open_testdata('info_from_spec_section_5_8.json'))
        self.maxDiff = 4000
        self.assertEqual(reparsed_json, example_json)

    def test21_write_profile(self):
        """Test writing of profile information."""
        i = IIIFInfo(api_version='3.0',
                     id="https://example.org/svc/a", width=1, height=2,
                     profile='pfl')
        j = json.loads(i.as_json())
        self.assertEqual(j['profile'], 'pfl')

    def test22_write_extra_info(self):
        i = IIIFInfo(api_version='3.0',
                     id="https://example.org/svc/a", width=1, height=2,
                     extra_qualities=['aaa1', 'aaa2'])
        j = json.loads(i.as_json())
        self.assertEqual(j['profile'], 'level1')
        self.assertNotIn('extraFormats', j)
        self.assertEqual(j['extraQualities'], ['aaa1', 'aaa2'])
        self.assertNotIn('extraFeatures', j)

