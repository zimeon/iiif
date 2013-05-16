"""Test code for i3f_info.py"""
import unittest

from i3f.info import I3fInfo

class TestAll(unittest.TestCase):

    def test_1_minmal(self):
        # Just do the trivial XML test
        # ?? should this empty case raise and error instead?
        ir = I3fInfo()
        self.assertEqual( ir.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<info xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n</info>')
        self.assertEqual( ir.as_json(), '{}' )
        ir = I3fInfo(width=100,height=200)
        self.assertEqual( ir.as_xml(), '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<info xmlns="http://library.stanford.edu/iiif/image-api/ns/">\n<width>100</width>\n<height>200</height>\n</info>')
        self.assertEqual( ir.as_json(), '{\n  "height": 200, \n  "width": 100\n}' )

    def test_2_scale_factor(self):
        ir = I3fInfo(width=1,height=2,scale_factors=[1,2])
        self.assertRegexpMatches( ir.as_xml(), r'<scale_factors>\n?<scale_factor>1</scale_factor>' )
        self.assertRegexpMatches( ir.as_json(), r'"scale_factors": \[\s*1' ) #,\s*2\s*]' )

# If run from command line, do tests
if __name__ == '__main__':
    unittest.main()
