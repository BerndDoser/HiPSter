import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from .wavelength_to_rgb import wavelength_to_rgb

matplotlib.use("Agg")


class SpectrumPlotter:

    def __init__(
        self,
        wavelengths: np.ndarray,
        axis: bool = False,
        ylim: tuple | None = None,
        figsize_in_pixel: int = 800,
        dpi: int = 96,
    ):
        """Plot a spectrum with a spectral colormap in the background.

        Args:
            wavelengths (np.ndarray): Wavelengths of the spectrum.
            axis (bool, optional): Print axis labels. Defaults to False.
            ylim (tuple, optional): Y-axis limits. Defaults to (0.0, 1.0).
            figsize_in_pixel (int, optional): Size of the figure in pixels. Defaults to 800.
            dpi (int, optional): Dots per inch. Defaults to 96.
        """
        self.wavelengths = wavelengths
        self.axis = axis
        self.ylim = ylim
        self.figsize = figsize_in_pixel / dpi
        self.dpi = dpi

        self.clim = (350, 780)
        norm = plt.Normalize(*self.clim)
        wl = np.arange(self.clim[0], self.clim[1] + 1, 2)
        colorlist = list(zip(norm(wl), [wavelength_to_rgb(w) for w in wl]))
        self.spectralmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "spectrum", colorlist
        )

    def __call__(self, spectrum: np.ndarray):

        fig, ax = plt.subplots(figsize=(self.figsize, self.figsize), dpi=self.dpi)
        # fig = plt.figure(figsize=(self.figsize, self.figsize), dpi=self.dpi)
        # ax = fig.gca()
        # ax.axis("tight")

        # Create the spectrum plot up to 10% above the maximum intensity to avoid artifacts in the image
        spectrum_max = max(1.0, np.max(spectrum) * 1.1)
        ax.plot(self.wavelengths, spectrum, color="black", linewidth=0.5)

        y = np.linspace(0, spectrum_max, 100)
        X, Y = np.meshgrid(self.wavelengths, y)

        extent = (
            np.min(self.wavelengths),
            np.max(self.wavelengths),
            np.min(y),
            np.max(y),
        )

        ax.imshow(
            X, clim=self.clim, extent=extent, cmap=self.spectralmap, aspect="auto"
        )
        # Fill the area above the spectrum with white. Add 10% to avoid artifacts in the image.
        ax.fill_between(self.wavelengths, spectrum, spectrum_max * 1.1, color="w")

        if self.ylim:
            ax.set_ylim(self.ylim)

        if self.axis:
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity")
        else:
            ax.axis("off")

        plt.subplots_adjust(0, 0, 1, 1, 0, 0)

        canvas = fig.canvas
        canvas.draw_idle()
        data = np.frombuffer(canvas.tostring_argb(), dtype="uint8")
        data = data.reshape(*reversed(canvas.get_width_height()), 4)[:, :, 1:4]

        plt.close(fig)
        return data
