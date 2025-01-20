import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from .wavelength_to_rgb import wavelength_to_rgb

matplotlib.use("Agg")


class AbsorptionLinePlotter:

    def __init__(
        self,
        wavelengths: np.ndarray,
        axis: bool = False,
        ylim: tuple | None = None,
        figsize_in_pixel: int = 800,
        dpi: int = 96,
        return_type: str = "ndarray",
    ):
        """Plot a spectrum with a spectral colormap in the background.

        Args:
            wavelengths (np.ndarray): Wavelengths of the spectrum.
            axis (bool, optional): Print axis labels. Defaults to False.
            ylim (tuple, optional): Y-axis limits. Defaults to (0.0, 1.0).
            figsize_in_pixel (int, optional): Size of the figure in pixels. Defaults to 800.
            dpi (int, optional): Dots per inch. Defaults to 96.
            return_type (str, optional): Type of return value ['plot', 'ndarray']. Defaults to "ndarray".
        """
        self.wavelengths = wavelengths
        self.axis = axis
        self.ylim = ylim
        self.figsize = figsize_in_pixel / dpi
        self.dpi = dpi
        self.return_type = return_type

    def __call__(self, flux: np.ndarray):

        height = 100  # how "tall" you want the 2D image
        n_wl = len(self.wavelengths)
        # Initialize (height, n_wl, 3) for an RGB image
        spectrum_image_rgb = np.zeros((height, n_wl, 3))
        for i, wl in enumerate(self.wavelengths):
            base_color = wavelength_to_rgb(wl, gamma=0.8)
            # Scale the color by flux to adjust brightness
            # You could adjust scaling or normalization here if needed.
            color_col = [c * flux[i] for c in base_color]

            # Fill this column (all rows in column i have the same color)
            spectrum_image_rgb[:, i, :] = color_col

        fig, ax = plt.subplots(figsize=(self.figsize, self.figsize), dpi=self.dpi)
        fig.tight_layout()

        ax.imshow(spectrum_image_rgb, origin="lower", aspect="auto")
        # ax.axis("off")

        if self.return_type == "plot":
            return ax
        elif self.return_type == "ndarray":
            canvas = fig.canvas
            canvas.draw_idle()
            data = np.frombuffer(canvas.tostring_argb(), dtype="uint8")
            data = data.reshape(*reversed(canvas.get_width_height()), 4)[:, :, 1:4]
            return data
        else:
            raise RuntimeError("Invalid return type. Choose 'axes' or 'ndarray'.")
