from __future__ import print_function, division

import numpy as np
from numpy.testing import (run_module_suite, assert_array_almost_equal,
                           assert_almost_equal, assert_array_equal,
                           assert_raises)
import warnings

from skimage.restoration import unwrap_phase


def assert_phase_almost_equal(a, b, *args, **kwargs):
    '''An assert_almost_equal insensitive to phase shifts of n*2*pi.'''
    shift = 2 * np.pi * np.round((b.mean() - a.mean()) / (2 * np.pi))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print('assert_phase_allclose, abs', np.max(np.abs(a - (b - shift))))
        print('assert_phase_allclose, rel',
              np.max(np.abs((a - (b - shift)) / a)))
    if np.ma.isMaskedArray(a):
        assert np.ma.isMaskedArray(b)
        assert_array_equal(a.mask, b.mask)
        au = np.asarray(a)
        bu = np.asarray(b)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            print('assert_phase_allclose, no mask, abs',
                  np.max(np.abs(au - (bu - shift))))
            print('assert_phase_allclose, no mask, rel',
                  np.max(np.abs((au - (bu - shift)) / au)))
    assert_array_almost_equal(a + shift, b, *args, **kwargs)


def check_unwrap(image, mask=None):
    image_wrapped = np.angle(np.exp(1j * image))
    if not mask is None:
        print('Testing a masked image')
        image = np.ma.array(image, mask=mask)
        image_wrapped = np.ma.array(image_wrapped, mask=mask)
    image_unwrapped = unwrap_phase(image_wrapped)
    assert_phase_almost_equal(image_unwrapped, image)


def test_unwrap_1d():
    image = np.linspace(0, 10 * np.pi, 100)
    check_unwrap(image)
    # Masked arrays are not allowed in 1D
    assert_raises(ValueError, check_unwrap, image, True)
    # wrap_around is not allowed in 1D
    assert_raises(ValueError, unwrap_phase, image, True)


def test_unwrap_2d():
    x, y = np.ogrid[:8, :16]
    image = 2 * np.pi * (x * 0.2 + y * 0.1)
    yield check_unwrap, image
    mask = np.zeros(image.shape, dtype=np.bool)
    mask[4:6, 4:8] = True
    yield check_unwrap, image, mask


def test_unwrap_3d():
    x, y, z = np.ogrid[:8, :12, :16]
    image = 2 * np.pi * (x * 0.2 + y * 0.1 + z * 0.05)
    yield check_unwrap, image
    mask = np.zeros(image.shape, dtype=np.bool)
    mask[4:6, 4:6, 1:3] = True
    yield check_unwrap, image, mask


def check_wrap_around(ndim, axis):
    # create a ramp, but with the last pixel along axis equalling the first
    elements = 100
    ramp = np.linspace(0, 12 * np.pi, elements)
    ramp[-1] = ramp[0]
    image = ramp.reshape(tuple([elements if n == axis else 1
                                for n in range(ndim)]))
    image_wrapped = np.angle(np.exp(1j * image))

    index_first = tuple([0] * ndim)
    index_last = tuple([-1 if n == axis else 0 for n in range(ndim)])
    # unwrap the image without wrap around
    with warnings.catch_warnings():
        # We do not want warnings about length 1 dimensions
        warnings.simplefilter("ignore")
        image_unwrap_no_wrap_around = unwrap_phase(image_wrapped)
    print('endpoints without wrap_around:',
          image_unwrap_no_wrap_around[index_first],
          image_unwrap_no_wrap_around[index_last])
    # without wrap around, the endpoints of the image should differ
    assert abs(image_unwrap_no_wrap_around[index_first]
               - image_unwrap_no_wrap_around[index_last]) > np.pi
    # unwrap the image with wrap around
    wrap_around = [n == axis for n in range(ndim)]
    with warnings.catch_warnings():
        # We do not want warnings about length 1 dimensions
        warnings.simplefilter("ignore")
        image_unwrap_wrap_around = unwrap_phase(image_wrapped, wrap_around)
    print('endpoints with wrap_around:',
          image_unwrap_wrap_around[index_first],
          image_unwrap_wrap_around[index_last])
    # with wrap around, the endpoints of the image should be equal
    assert_almost_equal(image_unwrap_wrap_around[index_first],
                        image_unwrap_wrap_around[index_last])


def test_wrap_around():
    for ndim in (2, 3):
        for axis in range(ndim):
            yield check_wrap_around, ndim, axis


def test_mask():
    length = 100
    ramps = [np.linspace(0, 4 * np.pi, length),
             np.linspace(0, 8 * np.pi, length),
             np.linspace(0, 6 * np.pi, length)]
    image = np.vstack(ramps)
    mask_1d = np.ones((length,), dtype=np.bool)
    mask_1d[0] = mask_1d[-1] = False
    for i in range(len(ramps)):
        # mask all ramps but the i'th one
        mask = np.zeros(image.shape, dtype=np.bool)
        mask |= mask_1d.reshape(1, -1)
        mask[i, :] = False   # unmask i'th ramp
        image_wrapped = np.ma.array(np.angle(np.exp(1j * image)), mask=mask)
        image_unwrapped = unwrap_phase(image_wrapped)
        image_unwrapped -= image_unwrapped[0, 0]    # remove phase shift
        # The end of the unwrapped array should have value equal to the
        # endpoint of the unmasked ramp
        assert_array_almost_equal(image_unwrapped[:, -1], image[i, -1])

        # Same tests, but forcing use of the 3D unwrapper by reshaping
        image_wrapped_3d = image_wrapped.reshape((1,) + image_wrapped.shape)
        image_unwrapped_3d = unwrap_phase(image_wrapped_3d)
        image_unwrapped_3d -= image_unwrapped_3d[0, 0, 0]  # remove phase shift
        assert_array_almost_equal(image_unwrapped_3d[:, :, -1], image[i, -1])


if __name__ == "__main__":
    run_module_suite()