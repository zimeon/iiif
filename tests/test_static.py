"""Test code for iiif.static."""
import os
import os.path
import re
import shutil
import tempfile
import unittest
import sys
import contextlib
from testfixtures import LogCapture
try:  # python2
    # Must try this first as io also exists in python2
    # but is the wrong one!
    import StringIO as io
except ImportError:  # python3
    import io

from iiif.static import IIIFStatic, IIIFStaticError, static_partial_tile_sizes, static_full_sizes


class MyLogCapture(LogCapture):
    """LogCapture class with added all_msgs property."""

    @property
    def all_msgs(self):
        """Return string with all messages recorded."""
        msgs = ''
        for r in self.records:
            msgs += r.msg
        return(msgs)


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_init(self):
        """Test initialization."""
        s = IIIFStatic()
        self.assertEqual(s.api_version, '2.0')  # default is 2.0
        self.assertEqual(s.tilesize, 512)
        s = IIIFStatic(src='abc', dst='def', tilesize=1024,
                       api_version='2', dryrun=True)
        self.assertEqual(s.src, 'abc')
        self.assertEqual(s.dst, 'def')
        self.assertEqual(s.tilesize, 1024)
        self.assertEqual(s.api_version, '2.0')
        self.assertEqual(s.dryrun, True)
        s = IIIFStatic(src='abc', dst='def', tilesize=1024,
                       api_version='1', dryrun=True)
        self.assertEqual(s.api_version, '1.1')

    def test02_get_osd_config(self):
        """Test get_osd_config."""
        s = IIIFStatic()
        self.assertEqual(s.get_osd_config('2.0.0')['use_canonical'], True)
        self.assertRaises(IIIFStaticError, s.get_osd_config, 'abc')
        self.assertRaises(IIIFStaticError, s.get_osd_config, '0.0.0')

    def test03_generate(self):
        """Test generation of a static image."""
        # dryrun covers most
        tmp1 = tempfile.mkdtemp()
        os.mkdir(os.path.join(tmp1, 'a'))
        try:
            # no canonical syntax with osd_version='1.0.0'
            s = IIIFStatic(dst=tmp1, tilesize=512,
                           api_version='1.1', osd_version='1.0.0', dryrun=True)
            with MyLogCapture('iiif.static') as lc:
                s.generate(src='testimages/starfish_1500x2000.png',
                           identifier='a')
            self.assertTrue(re.search(' / a/info.json', lc.all_msgs))
            self.assertTrue(
                re.search(' / a/1024,1536,476,464/476,464/0/native.jpg', lc.all_msgs))
            # largest full region (and symlink from w,h)
            self.assertTrue(
                re.search(' / a/full/375,500/0/native.jpg', lc.all_msgs))
            # smallest full region
            self.assertTrue(
                re.search(' / a/full/1,1/0/native.jpg', lc.all_msgs))
            # v2.0
            s = IIIFStatic(dst=tmp1, tilesize=512,
                           api_version='2.0', dryrun=True)
            with MyLogCapture('iiif.static') as lc:
                s.generate(src='testimages/starfish_1500x2000.png',
                           identifier='a')
            self.assertTrue(re.search(' / a/info.json', lc.all_msgs))
            self.assertTrue(
                re.search(' / a/1024,1536,476,464/476,/0/default.jpg', lc.all_msgs))
            # largest full region (and symlink from w,h)
            self.assertTrue(
                re.search(' / a/full/375,/0/default.jpg', lc.all_msgs))
            self.assertTrue(
                re.search(' / a/full/375,500 -> a/full/375,', lc.all_msgs))
            # smallest full region
            self.assertTrue(
                re.search(' / a/full/1,/0/default.jpg', lc.all_msgs))
            self.assertTrue(
                re.search(' / a/full/1,1 -> a/full/1,', lc.all_msgs))
        finally:
            shutil.rmtree(tmp1)
        # real write
        tmp2 = tempfile.mkdtemp()
        try:
            s = IIIFStatic(dst=tmp2, tilesize=1024, api_version='2.0')
            with MyLogCapture('iiif.static') as lc:
                s.generate(src='testimages/starfish_1500x2000.png',
                           identifier='b')
            self.assertTrue(os.path.isfile(os.path.join(tmp2, 'b/info.json')))
            self.assertTrue(os.path.isfile(os.path.join(
                tmp2, 'b/1024,1024,476,976/476,/0/default.jpg')))
            self.assertTrue(os.path.isfile(
                os.path.join(tmp2, 'b/full/1,/0/default.jpg')))
        finally:
            shutil.rmtree(tmp2)

    def test04_generate_tile(self):
        """Test generation of a tile."""
        # most tested via other calls, make sure zero size skip works
        tmp1 = tempfile.mkdtemp()
        os.mkdir(os.path.join(tmp1, 'a'))
        try:
            s = IIIFStatic(dst=tmp1, tilesize=512, api_version='2.0')
            s.identifier = 'fgh'
            s.src = 'testimages/starfish_1500x2000.png'
            with MyLogCapture('iiif.static') as lc:
                s.generate_tile(region='full', size=[0, 1])
            self.assertTrue(re.search(r'zero size, skipped', lc.all_msgs))
        finally:
            shutil.rmtree(tmp1)

    def _generate_tile_sizes(self, width, height, tilesize, scale_factors, canonical=False):
        # Make easy-to check list of sizes...
        sizes = set()
        for (region, size) in static_partial_tile_sizes(width, height, tilesize, scale_factors):
            # should never have zero size w or h
            self.assertNotEqual(size[0], 0)
            self.assertNotEqual(size[1], 0)
            if (canonical):
                sizes.add(str(region) + '[' + str(size[0]) + ',]')
            else:
                sizes.add(str(region) + str(size))
        return sizes

    def test05_static_partial_tile_sizes(self):
        """Generate set of static tile sizes and check examples."""
        sizes = self._generate_tile_sizes(100, 100, 64, [1, 2, 4])
        # would use assertIn for >=2.7
        self.assertTrue('[0, 0, 64, 64][64, 64]' in sizes)
        self.assertTrue('[0, 64, 64, 36][64, 36]' in sizes)
        self.assertTrue('[64, 0, 36, 64][36, 64]' in sizes)
        self.assertTrue('[64, 64, 36, 36][36, 36]' in sizes)
        self.assertEqual(len(sizes), 4)
        # Test cases for 3467 by 5117 with osd 2.0.0
        # see https://gist.github.com/zimeon/d97bc554ead393b7588d
        sizes = self._generate_tile_sizes(3467, 5117, 512, [1, 2, 4, 8], True)
        # print(sizes)
        self.assertTrue('[0, 0, 1024, 1024][512,]' in sizes)
        self.assertTrue('[0, 0, 2048, 2048][512,]' in sizes)
        self.assertTrue('[0, 0, 3467, 4096][434,]' in sizes)
        self.assertTrue('[0, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 1024, 1024, 1024][512,]' in sizes)
        self.assertTrue('[0, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 2048, 1024, 1024][512,]' in sizes)
        self.assertTrue('[0, 2048, 2048, 2048][512,]' in sizes)
        self.assertTrue('[0, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 3072, 1024, 1024][512,]' in sizes)
        self.assertTrue('[0, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 4096, 1024, 1021][512,]' in sizes)
        self.assertTrue('[0, 4096, 2048, 1021][512,]' in sizes)
        self.assertTrue('[0, 4096, 3467, 1021][434,]' in sizes)
        self.assertTrue('[0, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[0, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[0, 512, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 0, 1024, 1024][512,]' in sizes)
        self.assertTrue('[1024, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 1024, 1024, 1024][512,]' in sizes)
        self.assertTrue('[1024, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 2048, 1024, 1024][512,]' in sizes)
        self.assertTrue('[1024, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 3072, 1024, 1024][512,]' in sizes)
        self.assertTrue('[1024, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 4096, 1024, 1021][512,]' in sizes)
        self.assertTrue('[1024, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[1024, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[1024, 512, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[1536, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[1536, 512, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 0, 1024, 1024][512,]' in sizes)
        self.assertTrue('[2048, 0, 1419, 2048][355,]' in sizes)
        self.assertTrue('[2048, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 1024, 1024, 1024][512,]' in sizes)
        self.assertTrue('[2048, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 2048, 1024, 1024][512,]' in sizes)
        self.assertTrue('[2048, 2048, 1419, 2048][355,]' in sizes)
        self.assertTrue('[2048, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 3072, 1024, 1024][512,]' in sizes)
        self.assertTrue('[2048, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 4096, 1024, 1021][512,]' in sizes)
        self.assertTrue('[2048, 4096, 1419, 1021][355,]' in sizes)
        self.assertTrue('[2048, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[2048, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[2048, 512, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[2560, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[2560, 512, 512, 512][512,]' in sizes)
        self.assertTrue('[3072, 0, 395, 1024][198,]' in sizes)
        self.assertTrue('[3072, 0, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 1024, 395, 1024][198,]' in sizes)
        self.assertTrue('[3072, 1024, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 1536, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 2048, 395, 1024][198,]' in sizes)
        self.assertTrue('[3072, 2048, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 2560, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 3072, 395, 1024][198,]' in sizes)
        self.assertTrue('[3072, 3072, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 3584, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 4096, 395, 1021][198,]' in sizes)
        self.assertTrue('[3072, 4096, 395, 512][395,]' in sizes)
        self.assertTrue('[3072, 4608, 395, 509][395,]' in sizes)
        self.assertTrue('[3072, 512, 395, 512][395,]' in sizes)
        self.assertTrue('[512, 0, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 1024, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 1536, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 2048, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 2560, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 3072, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 3584, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 4096, 512, 512][512,]' in sizes)
        self.assertTrue('[512, 4608, 512, 509][512,]' in sizes)
        self.assertTrue('[512, 512, 512, 512][512,]' in sizes)

    def test06_static_full_sizes(self):
        """Test full region tiles."""
        # generate set of static tile sizes to look for examples in
        sizes = set()
        for (size) in static_full_sizes(100, 100, 64):
            # should never have zero size w or h
            self.assertNotEqual(size[0], 0)
            self.assertNotEqual(size[1], 0)
            sizes.add(str(size))
        self.assertFalse('[100, 100]' in sizes)
        self.assertTrue('[50, 50]' in sizes)
        self.assertTrue('[25, 25]' in sizes)
        self.assertTrue('[13, 13]' in sizes)
        self.assertTrue('[6, 6]' in sizes)
        self.assertTrue('[3, 3]' in sizes)
        self.assertTrue('[2, 2]' in sizes)
        self.assertTrue('[1, 1]' in sizes)
        self.assertEqual(len(sizes), 7)
        # but then if tile size is 512 we want 100 included
        sizes = set()
        for (size) in static_full_sizes(100, 100, 512):
            # should never have zero size w or h
            self.assertNotEqual(size[0], 0)
            self.assertNotEqual(size[1], 0)
            sizes.add(str(size))
        self.assertTrue('[100, 100]' in sizes)
        self.assertTrue('[50, 50]' in sizes)
        self.assertEqual(len(sizes), 8)

    def test07_setup_destination(self):
        """Test setip_destination."""
        s = IIIFStatic()
        # no dst
        self.assertRaises(Exception, s.setup_destination)
        # now really create dir
        tmp = tempfile.mkdtemp()
        try:
            # dst and no identifier
            s.src = 'a/b.ext'
            s.dst = os.path.join(tmp, 'xyz')
            s.identifier = None
            s.setup_destination()
            self.assertTrue(os.path.isdir(tmp))
            self.assertTrue(os.path.isdir(s.dst))
            self.assertTrue(os.path.isdir(os.path.join(s.dst, 'b')))
            self.assertEqual(s.identifier, 'b')
            # dst and identifier
            s.src = 'a/b.ext'
            s.dst = os.path.join(tmp, 'zyx')
            s.identifier = 'c'
            s.setup_destination()
            self.assertTrue(os.path.isdir(s.dst))
            self.assertTrue(os.path.isdir(os.path.join(s.dst, 'c')))
            self.assertEqual(s.identifier, 'c')
            # dst path is file
            s.dst = os.path.join(tmp, 'exists1')
            open(s.dst, 'w').close()
            self.assertRaises(Exception, s.setup_destination)
            # dst and identifier, path is file
            s.identifier = 'exists2'
            s.dst = tmp
            open(os.path.join(s.dst, s.identifier), 'w').close()
            self.assertRaises(Exception, s.setup_destination)
            # dst and identifier, both dirs exist and OK
            s.dst = tmp
            s.identifier = 'id1'
            os.mkdir(os.path.join(s.dst, s.identifier))
            s.setup_destination()  # nothing created, no exception
        finally:
            shutil.rmtree(tmp)

    def test08_write_html(self):
        """Test write_html."""
        s = IIIFStatic()
        # bad output dir
        self.assertRaises(Exception, s.write_html,
                          '/tmp/path_does_no_exist_(i_hope)')
        # write to good path
        tmp = tempfile.mkdtemp()
        s.identifier = 'abc1'
        s.write_html(tmp)
        self.assertTrue(os.path.isfile(os.path.join(tmp, 'abc1.html')))
        # write to subdir of good path
        tmp = tempfile.mkdtemp()
        s.identifier = 'abc2'
        tmp2 = os.path.join(tmp, 'xyz')
        s.write_html(tmp2)
        self.assertTrue(os.path.isfile(os.path.join(tmp2, 'abc2.html')))
        # write to good path with osd
        tmp = tempfile.mkdtemp()
        s.identifier = 'abc3'
        s.write_html(tmp, include_osd=True)
        self.assertTrue(os.path.isfile(os.path.join(tmp, 'abc3.html')))
        self.assertTrue(os.path.isfile(os.path.join(
            tmp, 'openseadragon200/openseadragon.min.js')))
        self.assertTrue(s.copied_osd)
        # add another, with osd already present (and marked as such)
        s.identifier = 'abc4'
        with LogCapture('iiif.static') as lc:
            s.write_html(tmp, include_osd=True)
        self.assertTrue(os.path.isfile(os.path.join(tmp, 'abc4.html')))
        self.assertTrue(os.path.isfile(os.path.join(
            tmp, 'openseadragon200/openseadragon.min.js')))
        self.assertTrue(s.copied_osd)
        self.assertEqual(lc.records[-1].msg, 'OpenSeadragon already copied')
        # add yet another, with osd already present (but not marked)
        s.identifier = 'abc5'
        s.copied_osd = False
        with LogCapture('iiif.static') as lc:
            s.write_html(tmp, include_osd=True)
        self.assertTrue(os.path.isfile(os.path.join(tmp, 'abc5.html')))
        self.assertTrue(os.path.isfile(os.path.join(
            tmp, 'openseadragon200/openseadragon.min.js')))
        self.assertTrue(s.copied_osd)
        self.assertTrue(re.search(r'OpenSeadragon images directory .* already exists',
                                  lc.records[-1].msg))
        # add another but with a prefix
        s.identifier = 'abc6'
        s.prefix = 'z/y/x'
        s.copied_osd = False
        s.write_html(tmp, include_osd=True)
        html_file = os.path.join(tmp, 'abc6.html')
        self.assertTrue(os.path.isfile(html_file))
        with open(html_file, 'r') as x:
            html = x.read()
        self.assertTrue(re.search(r'z/y/x/abc6/info.json', html))
        # bad write to existing path
        tmp = tempfile.mkdtemp()
        tmp2 = os.path.join(tmp, 'file')
        open(tmp2, 'w').close()
        s.identifier = 'abc4'
        self.assertRaises(Exception, s.write_html, tmp2)
