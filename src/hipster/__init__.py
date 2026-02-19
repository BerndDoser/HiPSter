import importlib.metadata

from .absorption_line_plotter import AbsorptionLinePlotter
from .hips_generator import HiPSGenerator
from .html_generator import HTMLGenerator
from .image_generator import ImageGenerator
from .image_plotter import ImagePlotter
from .inference import Inference
from .range import Range
from .spectrum_plotter import SpectrumPlotter
from .task import Task
from .votable_generator import VOTableGenerator

__version__ = importlib.metadata.version("astro-hipster")
__all__ = [
    "AbsorptionLinePlotter",
    "HiPSGenerator",
    "HTMLGenerator",
    "ImageGenerator",
    "ImagePlotter",
    "Inference",
    "Range",
    "SpectrumPlotter",
    "Task",
    "VOTableGenerator",
]
