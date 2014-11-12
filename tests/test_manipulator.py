"""Test code for null iiif.manipulator"""
import os
import shutil
import tempfile
import unittest

from iiif.manipulator import IIIFManipulator
from iiif.request import IIIFRequest

class TestAll(unittest.TestCase):

    def test01_init(self):
        m = IIIFManipulator()
        self.assertEqual( m.api_version, '2.0' )

    def test02_derive(self):
        m = IIIFManipulator()
        r = IIIFRequest()
        r.parse_url('id1/full/full/0/default')
        tmp = tempfile.mkdtemp()
        outfile = os.path.join(tmp,'testout.png')
        try:
            m.derive(srcfile='testimages/test1.png',
                     request=r, outfile=outfile);
            self.assertTrue( os.path.isfile(outfile) )
            self.assertEqual( os.path.getsize(outfile), 65810 )
        finally:
            shutil.rmtree(tmp) 
