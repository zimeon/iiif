"""Test code for PIL based IIIF image manipulator."""
import unittest
import tempfile
import os
import os.path
import re

from PIL import Image

from iiif.error import IIIFError
from iiif.manipulator_pil import IIIFManipulatorPIL
from iiif.request import IIIFRequest


class TestAll(unittest.TestCase):
    """Tests."""

    def test01_init(self):
        """Initialize."""
        m = IIIFManipulatorPIL()
        self.assertTrue(m.api_version)
        m = IIIFManipulatorPIL(api_version='2.0')
        self.assertEqual(m.api_version, '2.0')

    def test02_max_image_pizels(self):
        """Check function for setting max number of pixels."""
        m = IIIFManipulatorPIL()
        orig = Image.MAX_IMAGE_PIXELS
        m.set_max_image_pixels(12345)
        self.assertTrue(Image.MAX_IMAGE_PIXELS, 12345)
        m.set_max_image_pixels(0)
        self.assertTrue(Image.MAX_IMAGE_PIXELS, 12345)
        # check error raise with test image
        m.srcfile = 'testimages/test1.png'
        self.assertRaises(IIIFError, m.do_first)
        # back to normal
        m.set_max_image_pixels(orig)

    def test_do_first(self):
        """First step."""
        m = IIIFManipulatorPIL()
        # no image
        self.assertRaises(IIIFError, m.do_first)
        # add image, get size
        m.srcfile = 'testimages/test1.png'
        self.assertEqual(m.do_first(), None)
        self.assertEqual(m.width, 175)
        self.assertEqual(m.height, 131)
        # Errors
        # cannot do PDF
        m.srcfile = 'testimages/bad/pdf_example.pdf'
        try:  # could use assertRaisesRegexp in 2.7
            m.do_first()
        except IIIFError as e:
            self.assertTrue(re.match(r'''Failed to read image''', str(e)))
            self.assertTrue(re.search(r'''PIL: cannot identify image file''', str(e)))

    def test_do_region(self):
        """Region."""
        m = IIIFManipulatorPIL()
        # m.request = IIIFRequest()
        # m.request.region_full=True
        m.srcfile = 'testimages/test1.png'
        m.do_first()
        self.assertEqual(m.do_region(None, None, None, None), None)
        # noop, same w,h
        self.assertEqual(m.image.size, (175, 131))
        self.assertEqual(m.width, 175)
        self.assertEqual(m.height, 131)
        # select 100,50
        # m.request.region_full=False
        # m.request.region_xywh=(0,0,100,50)
        self.assertEqual(m.do_region(0, 0, 100, 50), None)
        self.assertEqual(m.width, 100)
        self.assertEqual(m.height, 50)

    def test_do_size(self):
        """Size."""
        m = IIIFManipulatorPIL()
        m.srcfile = 'testimages/test1.png'
        m.do_first()
        # noop
        self.assertEqual(m.do_size(None, None), None)
        self.assertEqual(m.image.size, (175, 131))
        self.assertEqual(m.width, 175)
        self.assertEqual(m.height, 131)
        # scale to 50%
        self.assertEqual(m.do_size(88, 66), None)
        self.assertEqual(m.image.size, (88, 66))
        self.assertEqual(m.width, 88)
        self.assertEqual(m.height, 66)

    def test_do_rotation(self):
        """Rotation."""
        m = IIIFManipulatorPIL()
        m.srcfile = 'testimages/test1.png'
        # noop, no rotation
        m.do_first()
        self.assertEqual(m.do_rotation(False, 0.0), None)
        self.assertEqual(m.image.size, (175, 131))
        # mirror - FIXME - tests only run, not image
        m.do_first()
        self.assertEqual(m.do_rotation(True, 0.0), None)
        self.assertEqual(m.image.size, (175, 131))
        # rotate
        m.do_first()
        self.assertEqual(m.do_rotation(False, 30.0), None)
        self.assertEqual(m.image.size, (218, 202))

    def test_do_quality(self):
        """Quality."""
        m = IIIFManipulatorPIL()
        m.srcfile = 'testimages/test1.png'
        # noop, no change
        m.do_first()
        self.assertEqual(m.do_quality(None), None)
        self.assertEqual(m.image.mode, 'RGB')
        # color is also no change
        m.do_first()
        self.assertEqual(m.do_quality('color'), None)
        self.assertEqual(m.image.mode, 'RGB')
        # grey and gray
        m.do_first()
        self.assertEqual(m.do_quality('grey'), None)
        self.assertEqual(m.image.mode, 'L')
        m.do_first()
        self.assertEqual(m.do_quality('gray'), None)
        self.assertEqual(m.image.mode, 'L')
        # bitonal
        m.do_first()
        self.assertEqual(m.do_quality('bitonal'), None)
        self.assertEqual(m.image.mode, '1')
        # test with image with palette (mode P in PIL)
        m = IIIFManipulatorPIL()
        m.srcfile = 'testimages/robot_palette_320x200.gif'
        m.do_first()
        self.assertEqual(m.do_quality('color'), None)
        self.assertEqual(m.image.mode, 'RGB')

    def test_do_format(self):
        """Format."""
        m = IIIFManipulatorPIL()
        m.srcfile = 'testimages/test1.png'
        # default is jpeg
        m.do_first()
        self.assertEqual(m.do_format(None), None)
        img = Image.open(m.outfile)
        self.assertEqual(img.format, 'JPEG')
        m.cleanup()
        # request jpeg
        self.assertEqual(m.do_format('jpg'), None)
        img = Image.open(m.outfile)
        self.assertEqual(img.format, 'JPEG')
        m.cleanup()
        # request png
        self.assertEqual(m.do_format('png'), None)
        img = Image.open(m.outfile)
        self.assertEqual(img.format, 'PNG')
        m.cleanup()
        # request webp
        self.assertEqual(m.do_format('webp'), None)
        img = Image.open(m.outfile)
        self.assertEqual(img.format, 'WEBP')
        m.cleanup()
        # request tiff, not supported
        self.assertRaises(IIIFError, m.do_format, 'tif')
        # request jp2, not supported
        self.assertRaises(IIIFError, m.do_format, 'jp2')
        # request other, not supported
        self.assertRaises(IIIFError, m.do_format, 'other')
        # save to specific location
        m.outfile = tempfile.NamedTemporaryFile(delete=True).name
        self.assertFalse(os.path.exists(m.outfile))  # check setup
        m.do_first()
        self.assertEqual(m.do_format(None), None)
        self.assertTrue(os.path.exists(m.outfile))

    def test_cleanup(self):
        """Cleanup."""
        m = IIIFManipulatorPIL()
        m.outtmp = None
        self.assertEqual(m.cleanup(), None)
        m.outtmp = '/this_will_not_exits_really_I_hope'
        self.assertEqual(m.cleanup(), None)
        # FIXME - check log here
