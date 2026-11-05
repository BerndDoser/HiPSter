import re

import pytest

from hipster import ColorMap


def test_colors():
    colors = ColorMap(column="sersic_n_i", vmin=0.2, vmax=10, log=True).colors(16)

    assert len(colors) == 16
    assert all(re.fullmatch("#[0-9a-f]{6}", color) for color in colors)


def test_invalid_range():
    with pytest.raises(ValueError, match="vmin must be smaller than vmax"):
        ColorMap(column="sersic_n_i", vmin=10, vmax=0.2)
    with pytest.raises(ValueError, match="vmin must be positive"):
        ColorMap(column="sersic_n_i", vmin=0, vmax=10, log=True)
