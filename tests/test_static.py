"""Test code for iiif.tatic"""
import os
import os.path
import re
import shutil
import tempfile
import unittest
import sys, StringIO, contextlib

from iiif.static import IIIFStatic, static_partial_tile_sizes, static_full_sizes

# From http://stackoverflow.com/questions/2654834/capturing-stdout-within-the-same-process-in-python
class Data(object):
    pass

@contextlib.contextmanager
def capture_stdout():
    old = sys.stdout
    capturer = StringIO.StringIO()
    sys.stdout = capturer
    data = Data()
    yield data
    sys.stdout = old
    data.result = capturer.getvalue()

class TestAll(unittest.TestCase):

    def test01_init(self):
        s=IIIFStatic()
        self.assertEqual( s.api_version,'1.1' )
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
        tmp = tempfile.mkdtemp()
        try:
            s=IIIFStatic( src='testimages/starfish_1500x2000.png', dst=tmp, tilesize=1024, api_version='1', dryrun=True )
            with capture_stdout() as capturer:
                s.generate(identifier='a')
            self.assertTrue( re.search(' / a/1024,1024,476,976/476,/0/native.jpg', capturer.result ))
            self.assertTrue( re.search(' / a/full/1,/0/native.jpg', capturer.result ))
        finally:
            shutil.rmtree(tmp)

    def test03_static_partial_tile_sizes(self):
        # generate set of static tile sizes to look for examples in
        sizes = set()
        for (region,size) in static_partial_tile_sizes(100,100,64,[1,2,4]):
            # should never have zero size w or h
            self.assertNotEqual( size[0], 0 )
            self.assertNotEqual( size[1], 0 )
            sizes.add( str(region)+str(size) )
        self.assertTrue( '[0, 0, 64, 64][64, 64]' in sizes ) #would use assertIn for >=2.7
        self.assertTrue( '[0, 64, 64, 36][64, 36]' in sizes )
        self.assertTrue( '[64, 0, 36, 64][36, 64]' in sizes )
        self.assertTrue( '[64, 64, 36, 36][36, 36]' in sizes )
        self.assertEqual( len(sizes), 4 )

    def test04_static_full_sizes(self):
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

    def test05_setup_destination(self):
        s=IIIFStatic()
        # no dst
        self.assertRaises( Exception, s.setup_destination )
        # now really create dir
        tmp = tempfile.mkdtemp()
        try:
            # dst and no identifier
            s.dst=os.path.join(tmp,'xyz')
            s.identifier=None
            s.setup_destination()
            self.assertTrue( os.path.isdir(s.dst) )
            self.assertEqual( s.outd, tmp )
            self.assertEqual( s.identifier, 'xyz' )
            # dst and identifier
            s.dst=os.path.join(tmp,'zyx')
            s.identifier='abc'
            s.setup_destination()
            self.assertTrue( os.path.isdir(s.dst) )
            self.assertTrue( os.path.isdir(os.path.join(s.dst,'abc')) )
            self.assertEqual( s.outd, s.dst )
            self.assertEqual( s.identifier, 'abc' )
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
            s.outd=None
            s.dst=tmp
            s.identifier='id1'
            os.mkdir( os.path.join(s.dst,s.identifier) )
            s.setup_destination()
            self.assertEqual( s.outd, tmp )
        finally:
            shutil.rmtree(tmp)
