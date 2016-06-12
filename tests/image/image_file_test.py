# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import pytest

from file_metadata.image.image_file import ImageFile
from tests import fetch_file, unittest


class ImageFileTest(unittest.TestCase):

    def test_ndarray_read(self):
        _file = ImageFile(fetch_file('ball.png'))
        self.assertEqual(_file.fetch('ndarray').shape, (226, 226, 4))

    def test_huge_ndarray(self):
        _file = ImageFile(fetch_file('huge.png'))
        self.assertEqual(_file.fetch('ndarray').shape, (0,))


class ImageFileSoftwaresTest(unittest.TestCase):

    def test_created_with_unknown(self):
        _file = ImageFile(fetch_file('red.svg'))
        self.assertEqual(_file.analyze_softwares(), {})

    def test_created_with_inkscape(self):
        _file = ImageFile(fetch_file('created_with_inkscape.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Inkscape')

    def test_created_with_matlab(self):
        _file = ImageFile(fetch_file('created_with_matlab.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'MATLAB')

    def test_created_with_imagemagick(self):
        _file = ImageFile(fetch_file('created_with_imagemagick.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'ImageMagick')

    def test_created_with_adobe_imageready(self):
        _file = ImageFile(fetch_file('created_with_adobe_imageready.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe ImageReady')

    def test_created_with_adobe_photoshop(self):
        _file = ImageFile(fetch_file('created_with_adobe_photoshop.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop')

    def test_created_with_adobe_photoshop_express(self):
        _file = ImageFile(fetch_file(
            'created_with_adobe_photoshop_express.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop Express')

    def test_created_with_adobe_photoshop_elements(self):
        _file = ImageFile(fetch_file(
            'created_with_adobe_photoshop_elements.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Adobe Photoshop Elements')

    def test_created_with_picasa(self):
        _file = ImageFile(fetch_file('created_with_picasa.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Picasa')

    def test_created_with_gimp(self):
        _file = ImageFile(fetch_file('created_with_gimp.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GIMP')

    def test_created_with_gnu_octave(self):
        _file = ImageFile(fetch_file('created_with_gnu_octave.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GNU Plot')

    def test_created_with_gnuplot(self):
        _file = ImageFile(fetch_file('created_with_gnuplot.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'GNU Plot')

    def test_created_with_chemtool(self):
        _file = ImageFile(fetch_file('created_with_chemtool.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Chemtool')

    def test_created_with_vectorfieldplot(self):
        _file = ImageFile(fetch_file('created_with_vectorfieldplot.svg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'VectorFieldPlot')

    def test_created_with_stella(self):
        _file = ImageFile(fetch_file('created_with_stella.png'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Stella')

    def test_created_with_microsoft_image_composite_editor(self):
        _file = ImageFile(fetch_file(
            'created_with_microsoft_image_composite_editor.jpg'))
        data = _file.analyze_softwares().get('Composite:Softwares', None)
        self.assertEqual(data, 'Microsoft ICE')


class ImageFileColorAverageTest(unittest.TestCase):

    def test_color_average_rgb_image(self):
        data = ImageFile(fetch_file('red.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (255, 0, 0))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 17-1462 TPX (Flame)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (244, 81, 44))

    def test_color_average_rgba_image(self):
        data = ImageFile(fetch_file('ball.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (113.705, 113.705, 113.705))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 18-5102 TPX (Brushed Nickel)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (122, 118, 117))

    def test_color_average_greyscale_image(self):
        data = ImageFile(fetch_file('barcode.png')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (170.579, 170.579, 170.579))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 15-4306 TPX (Belgian Block)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (167, 173, 170))

    def test_color_average_animated_image(self):
        data = ImageFile(fetch_file('animated.gif')).analyze_color_average()
        self.assertEqual(data['Color:AverageRGB'], (227.326, 224.414, 224.414))
        self.assertEqual(data['Color:ClosestLabeledColor'],
                         'PMS 13-4108 TPX (Nimbus Cloud)')
        self.assertEqual(data['Color:ClosestLabeledColorRGB'], (223, 223, 227))


# Increase the timeout as the first time it will need to download the
# shape predictor data ~60MB
@pytest.mark.timeout(300)
class ImageFileFaceLandmarksTest(unittest.TestCase):

    def test_facial_landmarks_monkey_face(self):
        _file = ImageFile(fetch_file('monkey_face.jpg'))
        data = _file.analyze_facial_landmarks()
        self.assertEqual(data, {})

    def test_facial_landmarks_mona_lisa(self):
        _file = ImageFile(fetch_file('mona_lisa.jpg'))
        data = _file.analyze_facial_landmarks(with_landmarks=True)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)
        face = data['dlib:Faces'][0]

        self.assertEqual(face['left_eye'], (288, 252))
        self.assertEqual(face['right_eye'], (361, 251))
        self.assertEqual(face['nose'], (325, 318))
        self.assertEqual(face['mouth'], (321, 338))

    def test_facial_landmarks_baby_face(self):
        _file = ImageFile(fetch_file('baby_face.jpg'))
        data = _file.analyze_facial_landmarks(with_landmarks=False)
        self.assertIn('dlib:Faces', data)
        self.assertEqual(len(data['dlib:Faces']), 1)

        face = data['dlib:Faces'][0]
        self.assertNotIn('left_eye', face)
        self.assertNotIn('right_eye', face)
        self.assertNotIn('nose', face)
        self.assertNotIn('mouth', face)
        self.assertIn('position', face)

    def test_facial_landmarks_animated_image(self):
        _file = ImageFile(fetch_file('animated.gif'))
        data = _file.analyze_facial_landmarks()
        self.assertEqual(data, {})


class ImageFileBarcodesTest(unittest.TestCase):

    def test_mona_lisa(self):
        _file = ImageFile(fetch_file('mona_lisa.jpg'))
        data = _file.analyze_barcode()
        self.assertEqual(data, {})

    def test_barcode(self):
        _file = ImageFile(fetch_file('barcode.png'))
        data = _file.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODABAR')
        self.assertEqual(data['zxing:Barcodes'][0]['data'], '137255')
        self.assertEqual(data['zxing:Barcodes'][0]['bounding box'],
                         {'width': 100, 'top': 29, 'height': 1, 'left': 4})

    def test_qrcode(self):
        _file = ImageFile(fetch_file('qrcode.jpg'))
        data = _file.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'QR_CODE')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'http://www.wikipedia.com')
        self.assertEqual(data['zxing:Barcodes'][0]['bounding box'],
                         {'width': 264, 'top': 52, 'height': 264, 'left': 50})

    def test_dmtx(self):
        _file = ImageFile(fetch_file('datamatrix.png'))
        data = _file.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 1)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'DATA_MATRIX')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         'Wikipedia, the free encyclopedia')

    def test_multiple_barcodes(self):
        _file = ImageFile(fetch_file('multibarcodes.png'))
        data = _file.analyze_barcode()
        self.assertIn('zxing:Barcodes', data)
        self.assertEqual(len(data['zxing:Barcodes']), 2)
        self.assertEqual(data['zxing:Barcodes'][0]['format'], 'CODE_128')
        self.assertEqual(data['zxing:Barcodes'][0]['data'],
                         '2LUS94941+67000000')
        self.assertEqual(data['zxing:Barcodes'][1]['format'], 'ITF')
        self.assertEqual(data['zxing:Barcodes'][1]['data'], '054804124097')

    def test_small_files(self):
        _file = ImageFile(fetch_file('static.gif'))
        self.assertEqual(_file.analyze_barcode(), {})
