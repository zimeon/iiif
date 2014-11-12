"""Test code for iiif.tatic"""
import shutil
import tempfile
import unittest

from iiif.static import IIIFStatic

class TestAll(unittest.TestCase):

    def test01_init(self):
        s=IIIFStatic()
        self.assertEqual( s.api_version,'1.1' )
        self.assertEqual( s.tilesize, 512 )
        s=IIIFStatic( src='abc', dst='def', prefix='ghi', tilesize=1024, api_version='2', dryrun=True )
        self.assertEqual( s.src, 'abc' )
        self.assertEqual( s.dst, 'def' )
        self.assertEqual( s.prefix, 'ghi' )
        self.assertEqual( s.tilesize, 1024 )
        self.assertEqual( s.api_version, '2.0' )
        self.assertEqual( s.dryrun, True )
        s=IIIFStatic( src='abc', dst='def', prefix='ghi', tilesize=1024, api_version='1', dryrun=True )
        self.assertEqual( s.api_version, '1.1' )

    def test02_generate(self):
        tmp = tempfile.mkdtemp()
        try:
            s=IIIFStatic( src='testimages/starfish_1500x2000.png', dst=tmp, prefix='pfx', tilesize=1024, api_version='1', dryrun=True )
            s.generate()
            print tmp
            self.assertEqual( tmp, 'a' )
        finally:
            shutil.rmtree(tmp) 

    def test03_generate_tile(self):
        pass

    def test04_setup_destination(self):
        pass

