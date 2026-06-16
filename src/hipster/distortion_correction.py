import math

import healpy
import numpy as np


def _calculate_pixels(matrix, pixel):
    """Calculates the pixel values for the HiPS tiling."""
    size = matrix.shape[0]
    if size > 1:
        matrix[: size // 2, : size // 2] = _calculate_pixels(matrix[: size // 2, : size // 2], pixel * 4)
        matrix[size // 2 :, : size // 2] = _calculate_pixels(matrix[size // 2 :, : size // 2], pixel * 4 + 1)
        matrix[: size // 2, size // 2 :] = _calculate_pixels(matrix[: size // 2, size // 2 :], pixel * 4 + 2)
        matrix[size // 2 :, size // 2 :] = _calculate_pixels(matrix[size // 2 :, size // 2 :], pixel * 4 + 3)
    else:
        matrix = pixel
    return matrix


def correct_distortion(data, order, pixel):
    """Corrects the distortion of the HiPS tiles."""
    size = data.shape[0]
    healpix_pixel = np.zeros((size, size), dtype=np.int64)
    healpix_pixel = _calculate_pixels(healpix_pixel, pixel)

    center_theta, center_phi = healpy.pix2ang(2**order, pixel, nest=True)  # theta 0...180 phi 0...360
    max_theta = max_phi = 2 * math.pi / (4 * 2**order) / 2

    # Vectorised healpy call — healpy is CPU-only, but accepts an array of pixels
    target_theta, target_phi = healpy.pix2ang(2**order * size, healpix_pixel.ravel(), nest=True)
    target_theta = target_theta.reshape(size, size)
    target_phi = target_phi.reshape(size, size)

    # Move array operations to GPU if CuPy is available, otherwise fall back to NumPy
    use_gpu = False
    try:
        import cupy as xp

        target_theta = xp.asarray(target_theta)
        target_phi = xp.asarray(target_phi)
        data = xp.asarray(data)
        use_gpu = True
    except ImportError:
        xp = np

    delta_theta = target_theta - center_theta
    delta_phi = xp.where(
        (center_phi == 0) & (target_phi > math.pi),
        (target_phi - 2 * math.pi) * xp.sin(target_theta),
        (target_phi - center_phi) * xp.sin(target_theta),
    )

    target_x = (size // 2 + delta_phi / max_phi * (size // 2 - 1)).astype(xp.int32)
    target_y = (size // 2 + delta_theta / max_theta * (size // 2 - 1)).astype(xp.int32)

    valid = (target_x >= 0) & (target_y >= 0) & (target_x < size) & (target_y < size)
    xs, ys = xp.where(valid)

    result = xp.zeros((size, size, 3), dtype=xp.uint8)
    result[xs, ys] = data[target_x[xs, ys], target_y[xs, ys]]

    return result.get() if use_gpu else result
