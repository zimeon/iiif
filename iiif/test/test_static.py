"""Test code for iiif.static"""
import os
import shutil
import tempfile
import unittest

from iiif.static import IIIFStatic

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
            s.generate()
        finally:
            shutil.rmtree(tmp) 

    def test03_generate_tile(self):
        pass

    def test04_setup_destination(self):
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
            self.assertTrue( Exception, s.setup_destination )
            # dst and identifier, path is file
            s.identifier='exists2'
            s.dst=tmp
            open(os.path.join(s.dst,s.identifier), 'w').close()
            self.assertTrue( Exception, s.setup_destination )
            # dst and identifier, both dirs exist and OK
            s.outd=None
            s.dst=tmp
            s.identifier='id1'
            os.mkdir( os.path.join(s.dst,s.identifier) )
            s.setup_destination()
            self.assertEqual( s.outd, tmp )
        finally:
            shutil.rmtree(tmp) 
