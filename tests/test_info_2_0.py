"""Test code for iiif/info.py for IIIF Image API 2.0."""
import unittest
from .testlib.assert_json_equal_mixin import AssertJSONEqual
import json
from iiif.info import IIIFInfo


class TestAll(unittest.TestCase, AssertJSONEqual):
    """Tests."""

    def test01_minmal(self):
        """Trivial JSON test."""
        # ?? should this empty case raise and error instead?
        ir = IIIFInfo(identifier="http://example.com/i1")
        self.assertJSONEqual(ir.as_json(
            validate=False), '{\n  "@context": "http://iiif.io/api/image/2/context.json", \n  "@id": "http://example.com/i1", \n  "profile": [\n    "http://iiif.io/api/image/2/level1.json"\n  ], \n  "protocol": "http://iiif.io/api/image"\n}')
        ir.width = 100
        ir.height = 200
        self.assertJSONEqual(ir.as_json(
        ), '{\n  "@context": "http://iiif.io/api/image/2/context.json", \n  "@id": "http://example.com/i1", \n  "height": 200, \n  "profile": [\n    "http://iiif.io/api/image/2/level1.json"\n  ], \n  "protocol": "http://iiif.io/api/image", \n  "width": 100\n}')

    def test04_conf(self):
        """Tile parameter configuration."""
        conf = {'tiles': [{'width': 999, 'scaleFactors': [9, 8, 7]}]}
        i = IIIFInfo(api_version='2.1', conf=conf)
        self.assertEqual(i.tiles[0]['width'], 999)
        self.assertEqual(i.tiles[0]['scaleFactors'], [9, 8, 7])
        # 1.1 style values
        self.assertEqual(i.tile_width, 999)
        self.assertEqual(i.scale_factors, [9, 8, 7])

    def test05_level_and_profile(self):
        """Test level and profile."""
        i = IIIFInfo()
        i.level = 0
        self.assertEqual(i.level, 0)
        self.assertEqual(i.compliance,
                         "http://iiif.io/api/image/2/level0.json")
        self.assertEqual(i.profile,
                         ["http://iiif.io/api/image/2/level0.json"])
        i.level = 2
        self.assertEqual(i.level, 2)
        self.assertEqual(i.compliance,
                         "http://iiif.io/api/image/2/level2.json")
        self.assertEqual(i.profile,
                         ["http://iiif.io/api/image/2/level2.json"])

    def test06_validate(self):
        """Test validate method."""
        i = IIIFInfo()
        self.assertRaises(Exception, i.validate, ())
        i = IIIFInfo(identifier='a')
        self.assertRaises(Exception, i.validate, ())
        i = IIIFInfo(identifier='a', width=1, height=2)
        self.assertTrue(i.validate())

    def test10_read_example_from_spec(self):
        """Test reading of example from spec."""
        i = IIIFInfo()
        fh = open('tests/testdata/info_json_2_0/info_from_spec.json')
        i.read(fh)
        self.assertEqual(i.context,
                         "http://iiif.io/api/image/2/context.json")
        self.assertEqual(i.id,
                         "http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol,
                         "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(i.sizes, [{"width": 150, "height": 100},
                                   {"width": 600, "height": 400},
                                   {"width": 3000, "height": 2000}])
        self.assertEqual(
            i.profile,
            ["http://iiif.io/api/image/2/level2.json",
             {"formats": ["gif", "pdf"],
              "qualities": ["color", "gray"],
              "supports": ["canonicalLinkHeader", "rotationArbitrary",
                           "profileLinkHeader", "http://example.com/feature/"]}])
        # extracted information
        self.assertEqual(i.compliance,
                         "http://iiif.io/api/image/2/level2.json")

    def test11_read_example_with_extra(self):
        """Test reading of example with extra data."""
        i = IIIFInfo()
        fh = open('tests/testdata/info_json_2_0/info_with_extra.json')
        i.read(fh)
        self.assertEqual(i.context, "http://iiif.io/api/image/2/context.json")
        self.assertEqual(
            i.id, "http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C")
        self.assertEqual(i.protocol, "http://iiif.io/api/image")
        self.assertEqual(i.width, 6000)
        self.assertEqual(i.height, 4000)
        self.assertEqual(
            i.tiles, [{"width": 512, "scaleFactors": [1, 2, 4, 8, 16]}])
        # and should have 1.1-like params too
        self.assertEqual(i.tile_width, 512)
        self.assertEqual(i.scale_factors, [1, 2, 4, 8, 16])
        self.assertEqual(i.compliance, "http://iiif.io/api/image/2/level2.json")

    def test12_read_unknown_context(self):
        """Test read with bad/unknown @context."""
        i = IIIFInfo()
        fh = open('tests/testdata/info_json_2_0/info_bad_context.json')
        self.assertRaises(Exception, i.read, fh)

    def test20_write_example_in_spec(self):
        """Test creation of example from spec."""
        i = IIIFInfo(
            id="http://www.example.org/image-service/abcd1234/1E34750D-38DB-4825-A38A-B60A345E591C",
            # "protocol" : "http://iiif.io/api/image",
            width=6000,
            height=4000,
            sizes=[
                {"width": 150, "height": 100},
                {"width": 600, "height": 400},
                {"width": 3000, "height": 2000}
            ],
            tiles=[
                {"width": 512, "scaleFactors": [1, 2, 4, 8, 16]}
            ],
            profile=["http://iiif.io/api/image/2/level2.json"],
            formats=["gif", "pdf"],
            qualities=["color", "gray"],
            supports=["canonicalLinkHeader", "rotationArbitrary",
                      "profileLinkHeader", "http://example.com/feature/"],
            service={
                "@context": "http://iiif.io/api/annex/service/physdim/1/context.json",
                "profile": "http://iiif.io/api/annex/service/physdim",
                "physicalScale": 0.0025,
                "physicalUnits": "in"
            }
        )
        reparsed_json = json.loads(i.as_json())
        example_json = json.load(
            open('tests/testdata/info_json_2_0/info_from_spec.json'))
        self.maxDiff = 4000
        self.assertEqual(reparsed_json, example_json)

    def test21_write_profile(self):
        """Test writing of profile information."""
        i = IIIFInfo(
            id="http://example.org/svc/a", width=1, height=2,
            profile=['pfl'], formats=["fmt1", "fmt2"])
        j = json.loads(i.as_json())
        self.assertEqual(len(j['profile']), 2)
        self.assertEqual(j['profile'][0], 'pfl')
        self.assertEqual(j['profile'][1], {'formats': ['fmt1', 'fmt2']})
        i = IIIFInfo(
            id="http://example.org/svc/a", width=1, height=2,
            profile=['pfl'], qualities=None)
        j = json.loads(i.as_json())
        self.assertEqual(len(j['profile']), 1)
        self.assertEqual(j['profile'][0], 'pfl')
        i = IIIFInfo(
            id="http://example.org/svc/a", width=1, height=2,
            profile=['pfl'], qualities=['q1', 'q2', 'q0'])
        j = json.loads(i.as_json())
        self.assertEqual(len(j['profile']), 2)
        self.assertEqual(j['profile'][0], 'pfl')
        self.assertEqual(j['profile'][1], {'qualities': ['q1', 'q2', 'q0']})
        i = IIIFInfo(
            id="http://example.org/svc/a", width=1, height=2,
            profile=['pfl'], supports=['a', 'b'])
        j = json.loads(i.as_json())
        self.assertEqual(len(j['profile']), 2)
        self.assertEqual(j['profile'][0], 'pfl')
        self.assertEqual(j['profile'][1], {'supports': ['a', 'b']})
        i = IIIFInfo(
            id="http://example.org/svc/a", width=1, height=2,
            profile=['pfl'], formats=["fmt1", "fmt2"],
            qualities=['q1', 'q2', 'q0'], supports=['a', 'b'])
        j = json.loads(i.as_json())
        self.assertEqual(len(j['profile']), 2)
        self.assertEqual(j['profile'][0], 'pfl')
        self.assertEqual(j['profile'][1]['formats'], ['fmt1', 'fmt2'])
        self.assertEqual(j['profile'][1]['qualities'], ['q1', 'q2', 'q0'])
        self.assertEqual(j['profile'][1]['supports'], ['a', 'b'])
