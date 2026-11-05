from dataclasses import dataclass

import matplotlib
import numpy as np


@dataclass
class ColorMap:
    """Colors the sources of a catalog by the values of a catalog column.

    Args:
        column (str): The catalog column defining the color.
        vmin (float): The value mapped to the lowest color, smaller values are clipped.
        vmax (float): The value mapped to the highest color, larger values are clipped.
        cmap (str, optional): The name of the matplotlib colormap. Defaults to "viridis".
        log (bool, optional): Use a logarithmic scale, non-positive values are invalid. Defaults to False.
        nan_color (str, optional): The color of sources with invalid values. Defaults to "#808080".
    """

    column: str
    vmin: float
    vmax: float
    cmap: str = "viridis"
    log: bool = False
    nan_color: str = "#808080"

    def __post_init__(self) -> None:
        if self.vmin >= self.vmax:
            raise ValueError(f"vmin must be smaller than vmax, got {self.vmin} and {self.vmax}")
        if self.log and self.vmin <= 0:
            raise ValueError(f"vmin must be positive for a logarithmic scale, got {self.vmin}")

    def colors(self, n: int = 64) -> list[str]:
        """Returns n equally spaced colors of the colormap as hex strings."""
        return [matplotlib.colors.to_hex(c) for c in matplotlib.colormaps[self.cmap](np.linspace(0, 1, n))]

    def as_dict(self) -> dict:
        """Returns the color map as dictionary for the HTML page."""
        return {
            "column": self.column,
            "vmin": self.vmin,
            "vmax": self.vmax,
            "log": self.log,
            "nan_color": self.nan_color,
            "colors": self.colors(),
        }
