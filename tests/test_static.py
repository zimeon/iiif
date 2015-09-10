"""Test code for iiif.static"""
import os
import os.path
import re
import shutil
import tempfile
import unittest
import sys
import contextlib
try: #python2
    # Must try this first as io also exists in python2
    # but in the wrong one!
    import StringIO as io
except ImportError: #python3
    import io

from iiif.static import IIIFStatic, static_partial_tile_sizes, static_full_sizes

# From http://stackoverflow.com/questions/2654834/capturing-stdout-within-the-same-process-in-python
class Data(object):
    pass

@contextlib.contextmanager
def capture_stdout():
    old = sys.stdout
    capturer = io.StringIO()
    sys.stdout = capturer
    data = Data()
    yield data
    sys.stdout = old
    data.result = capturer.getvalue()

class TestAll(unittest.TestCase):

    def test01_init(self):
        s=IIIFStatic()
        self.assertEqual( s.api_version,'2.0' ) # default is 2.0
        self.assertEqual( s.tilesize, 512 )
        s=IIIFStatic( src='abc', dst='def', tilesize=1024, api_version='2', dryrun=True )
        self.assertEqual( s.src, 'abc' )
        self.assertEqual( s.dst, 'def' )
        self.assertEqual( s.tilesize, 1024 )
        self.assertEqual( s.api_version, '2.0' )
        self.assertEqual( s.dryrun, True )
        s=IIIFStatic( src='abc', dst='def', tilesize=1024, api_version='1', dryrun=True )
        self.assertEqual( s.api_version, '1.1' )

    def test02_generate(self):
        # dryrun covers most
        tmp1 = tempfile.mkdtemp()
        os.mkdir( os.path.join(tmp1,'a') )
        try:
            s=IIIFStatic( dst=tmp1, tilesize=512, api_version='1.1', dryrun=True )
            with capture_stdout() as capturer:
                s.generate( src='testimages/starfish_1500x2000.png', identifier='a' )
            self.assertTrue( re.search(' / a/info.json', capturer.result ))
            self.assertTrue( re.search(' / a/1024,1536,476,464/476,/0/native.jpg', capturer.result ))
            self.assertTrue( re.search(' / a/full/1,/0/native.jpg', capturer.result ))
        finally:
            shutil.rmtree(tmp1)
        # real write 
        tmp2 = tempfile.mkdtemp()
        try:
            s=IIIFStatic( dst=tmp2, tilesize=1024, api_version='2.0' )
            with capture_stdout() as capturer:
                s.generate( src='testimages/starfish_1500x2000.png', identifier='b' )
            self.assertTrue( os.path.isfile(os.path.join(tmp2,'b/info.json')) )
            self.assertTrue( os.path.isfile(os.path.join(tmp2,'b/1024,1024,476,976/476,/0/default.jpg')) )
            self.assertTrue( os.path.isfile(os.path.join(tmp2,'b/full/1,/0/default.jpg')) )
        finally:
            shutil.rmtree(tmp2)

    def test03_generate_tile(self):
        # most tested via other calls, make sure zero size skip works
        tmp1 = tempfile.mkdtemp()
        os.mkdir( os.path.join(tmp1,'a') )
        try:
            s=IIIFStatic( dst=tmp1, tilesize=512, api_version='2.0' )
            s.identifier = 'fgh'
            s.src = 'testimages/starfish_1500x2000.png'
            with capture_stdout() as capturer:
                s.generate_tile( region='full', size=[0,1] )
            self.assertTrue( re.search(r'zero size, skipped', capturer.result) )
        finally:
            shutil.rmtree(tmp1)

    def _generate_tile_sizes(self,width,height,tilesize,scale_factors,canonical=False):
        sizes = set()
        for (region,size) in static_partial_tile_sizes(width,height,tilesize,scale_factors):
            # should never have zero size w or h
            self.assertNotEqual( size[0], 0 )
            self.assertNotEqual( size[1], 0 )
            if (canonical):
                sizes.add( str(region)+'['+str(size[0])+',]' )
            else:
                sizes.add( str(region)+str(size) )
        return sizes

    def test04_static_partial_tile_sizes(self):
        # generate set of static tile sizes to look for examples in
        sizes = self._generate_tile_sizes(100,100,64,[1,2,4])
        self.assertTrue( '[0, 0, 64, 64][64, 64]' in sizes ) #would use assertIn for >=2.7
        self.assertTrue( '[0, 64, 64, 36][64, 36]' in sizes )
        self.assertTrue( '[64, 0, 36, 64][36, 64]' in sizes )
        self.assertTrue( '[64, 64, 36, 36][36, 36]' in sizes )
        self.assertEqual( len(sizes), 4 )
        # Test cases for 3467 by 5117 with osd 2.0.0
        # see https://gist.github.com/zimeon/d97bc554ead393b7588d
        sizes = self._generate_tile_sizes(3467,5117,512,[1,2,4,8],True)
        #print(sizes)
        self.assertTrue( '[0, 0, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[0, 0, 2048, 2048][512,]' in sizes )
        self.assertTrue( '[0, 0, 3467, 4096][434,]' in sizes )
        self.assertTrue( '[0, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 1024, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[0, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 2048, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[0, 2048, 2048, 2048][512,]' in sizes )
        self.assertTrue( '[0, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 3072, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[0, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 4096, 1024, 1021][512,]' in sizes )
        self.assertTrue( '[0, 4096, 2048, 1021][512,]' in sizes )
        self.assertTrue( '[0, 4096, 3467, 1021][434,]' in sizes )
        self.assertTrue( '[0, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[0, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[0, 512, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 0, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[1024, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 1024, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[1024, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 2048, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[1024, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 3072, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[1024, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 4096, 1024, 1021][512,]' in sizes )
        self.assertTrue( '[1024, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[1024, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[1024, 512, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[1536, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[1536, 512, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 0, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[2048, 0, 1419, 2048][355,]' in sizes )
        self.assertTrue( '[2048, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 1024, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[2048, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 2048, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[2048, 2048, 1419, 2048][355,]' in sizes )
        self.assertTrue( '[2048, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 3072, 1024, 1024][512,]' in sizes )
        self.assertTrue( '[2048, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 4096, 1024, 1021][512,]' in sizes )
        self.assertTrue( '[2048, 4096, 1419, 1021][355,]' in sizes )
        self.assertTrue( '[2048, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[2048, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[2048, 512, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[2560, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[2560, 512, 512, 512][512,]' in sizes )
        self.assertTrue( '[3072, 0, 395, 1024][198,]' in sizes )
        self.assertTrue( '[3072, 0, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 1024, 395, 1024][198,]' in sizes )
        self.assertTrue( '[3072, 1024, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 1536, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 2048, 395, 1024][198,]' in sizes )
        self.assertTrue( '[3072, 2048, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 2560, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 3072, 395, 1024][198,]' in sizes )
        self.assertTrue( '[3072, 3072, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 3584, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 4096, 395, 1021][198,]' in sizes )
        self.assertTrue( '[3072, 4096, 395, 512][395,]' in sizes )
        self.assertTrue( '[3072, 4608, 395, 509][395,]' in sizes )
        self.assertTrue( '[3072, 512, 395, 512][395,]' in sizes )
        self.assertTrue( '[512, 0, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 1024, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 1536, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 2048, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 2560, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 3072, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 3584, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 4096, 512, 512][512,]' in sizes )
        self.assertTrue( '[512, 4608, 512, 509][512,]' in sizes )
        self.assertTrue( '[512, 512, 512, 512][512,]' in sizes )

    def test05_static_full_sizes(self):
        # generate set of static tile sizes to look for examples in
        sizes = set()
        for (size) in static_full_sizes(100,100,64):
            # should never have zero size w or h
            self.assertNotEqual( size[0], 0 )
            self.assertNotEqual( size[1], 0 )
            sizes.add( str(size) )
        self.assertFalse( '[100, 100]' in sizes )
        self.assertTrue( '[50, 50]' in sizes )
        self.assertTrue( '[25, 25]' in sizes )
        self.assertTrue( '[13, 13]' in sizes )
        self.assertTrue( '[6, 6]' in sizes )
        self.assertTrue( '[3, 3]' in sizes )
        self.assertTrue( '[2, 2]' in sizes )
        self.assertTrue( '[1, 1]' in sizes )
        self.assertEqual( len(sizes), 7 )

    def test06_setup_destination(self):
        s=IIIFStatic()
        # no dst
        self.assertRaises( Exception, s.setup_destination )
        # now really create dir
        tmp = tempfile.mkdtemp()
        try:
            # dst and no identifier
            s.src='a/b.ext'
            s.dst=os.path.join(tmp,'xyz')
            s.identifier=None
            s.setup_destination()
            self.assertTrue( os.path.isdir(tmp) )
            self.assertTrue( os.path.isdir(s.dst) )
            self.assertTrue( os.path.isdir(os.path.join(s.dst,'b')) )
            self.assertEqual( s.identifier, 'b' )
            # dst and identifier
            s.src='a/b.ext'
            s.dst=os.path.join(tmp,'zyx')
            s.identifier='c'
            s.setup_destination()
            self.assertTrue( os.path.isdir(s.dst) )
            self.assertTrue( os.path.isdir(os.path.join(s.dst,'c')) )
            self.assertEqual( s.identifier, 'c' )
            # dst path is file
            s.dst=os.path.join(tmp,'exists1')
            open(s.dst, 'w').close()
            self.assertRaises( Exception, s.setup_destination )
            # dst and identifier, path is file
            s.identifier='exists2'
            s.dst=tmp
            open(os.path.join(s.dst,s.identifier), 'w').close()
            self.assertRaises( Exception, s.setup_destination )
            # dst and identifier, both dirs exist and OK
            s.dst=tmp
            s.identifier='id1'
            os.mkdir( os.path.join(s.dst,s.identifier) )
            s.setup_destination() #nothing created, no exception
        finally:
            shutil.rmtree(tmp)

    def test07_write_html(self):
        s=IIIFStatic()
        # bad output dir
        self.assertRaises( Exception, s.write_html, '/tmp/path_does_no_exist_(i_hope)' )
        # write to good path
        tmp = tempfile.mkdtemp()
        s.identifier='abc1'
        s.write_html(tmp)
        self.assertTrue( os.path.isfile( os.path.join(tmp,'abc1.html') ) )
        # write to subdir of good path
        tmp = tempfile.mkdtemp()
        s.identifier='abc2'
        tmp2 = os.path.join(tmp,'xyz')
        s.write_html(tmp2)
        self.assertTrue( os.path.isfile( os.path.join(tmp2,'abc2.html') ) )
        # write to good path with osd
        tmp = tempfile.mkdtemp()
        s.identifier='abc3'
        s.write_html(tmp, include_osd=True)
        self.assertTrue( os.path.isfile( os.path.join(tmp,'abc3.html') ) )
        self.assertTrue( os.path.isfile( os.path.join(tmp,'osd/openseadragon.min.js') ) )
        # bad write to existing path
        tmp = tempfile.mkdtemp()
        tmp2 = os.path.join(tmp,'file')
        open(tmp2,'w').close()
        s.identifier='abc4'
        self.assertRaises( Exception, s.write_html, tmp2 )
