from ..bias import BiasSubtractor
from .utils import FakeImage, throws_inhomogeneous_set_exception
from ..stages import MasterCalibrationDoesNotExist
import pytest
import mock

import numpy as np


class FakeBiasImage(FakeImage):
    def __init__(self, *args, bias_level=0.0, **kwargs):
        super(FakeBiasImage, self).__init__(*args, image_multiplier=bias_level, **kwargs)
        self.header = {'BIASLVL': bias_level}


def test_no_input_images():
    subtractor = BiasSubtractor(None)
    images = subtractor.do_stage([])
    assert len(images) == 0


def test_group_by_keywords():
    subtractor = BiasSubtractor(None)
    assert subtractor.group_by_keywords == ['ccdsum']


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_header_has_biaslevel(mock_cal, mock_image):
    mock_image.return_value = FakeBiasImage()
    subtractor = BiasSubtractor(None)
    images = subtractor.do_stage([FakeImage() for x in range(6)])
    for image in images:
        assert image.header['BIASLVL'][0] == 0


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_header_biaslevel_is_1(mock_cal, mock_image):
    mock_image.return_value = FakeBiasImage(bias_level=1)
    subtractor = BiasSubtractor(None)
    images = subtractor.do_stage([FakeImage() for x in range(6)])
    for image in images:
        assert image.header['BIASLVL'][0] == 1


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_header_biaslevel_is_2(mock_cal, mock_image):
    mock_image.return_value = FakeBiasImage(bias_level=2.0)
    subtractor = BiasSubtractor(None)
    images = subtractor.do_stage([FakeImage() for x in range(6)])
    for image in images:
        assert image.header['BIASLVL'][0] == 2


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_raises_an_exection_if_ccdsums_are_different(mock_cal, mock_images):
    throws_inhomogeneous_set_exception(BiasSubtractor, None, 'ccdsum', '1 1')


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_raises_an_exection_if_epochs_are_different(mock_cal, mock_images):
    throws_inhomogeneous_set_exception(BiasSubtractor, None, 'epoch', '20160102')


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_raises_an_exection_if_nx_are_different(mock_cal, mock_images):
    mock_cal.return_value = 'test.fits'
    throws_inhomogeneous_set_exception(BiasSubtractor, None, 'nx', 105)


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_raises_an_exection_if_ny_are_different(mock_cal, mock_images):
    mock_cal.return_value = 'test.fits'
    throws_inhomogeneous_set_exception(BiasSubtractor, None, 'ny', 107)


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_raises_exception_if_no_master_calibration(mock_cal, mock_images):
    mock_cal.return_value = None
    mock_images.return_value = FakeBiasImage()
    subtractor = BiasSubtractor(None)

    with pytest.raises(MasterCalibrationDoesNotExist):
        images = subtractor.do_stage([FakeImage() for x in range(6)])


@mock.patch('banzai.stages.Image')
@mock.patch('banzai.stages.ApplyCalibration.get_calibration_filename')
def test_bias_subtraction_is_reasonable(mock_cal, mock_image):
    mock_cal.return_value = 'test.fits'
    input_bias = 1000.0
    input_readnoise = 9.0
    input_level = 2000.0
    nx = 101
    ny = 103

    fake_master_bias = FakeBiasImage(bias_level=input_bias)
    fake_master_bias.data = np.random.normal(0.0, input_readnoise, size=(ny, nx))
    mock_image.return_value = fake_master_bias

    subtractor = BiasSubtractor(None)
    images = [FakeImage(image_multiplier=input_level) for x in range(6)]

    images = subtractor.do_stage(images)

    for image in images:
        assert np.abs(image.header['BIASLVL'][0] - input_bias) < 1.0
        assert np.abs(np.mean(image.data) - input_level + input_bias) < 1.0
