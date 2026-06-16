import importlib.metadata

from .absorption_line_plotter import AbsorptionLinePlotter
from .dataset_projection import DatasetProjection
from .hips_generator import HiPSGenerator
from .html_generator import HTMLGenerator
from .image_generator import ImageGenerator
from .image_plotter import ImagePlotter
from .inference import Inference
from .numbered_hips_generator import NumberedHiPSGenerator
from .range import Range
from .spectrum_plotter import SpectrumPlotter
from .task import Task
from .votable_generator import VOTableGenerator

__version__ = importlib.metadata.version("astro-hipster")
__all__ = [
    "AbsorptionLinePlotter",
    "DatasetProjection",
    "HiPSGenerator",
    "HTMLGenerator",
    "ImageGenerator",
    "ImagePlotter",
    "Inference",
    "NumberedHiPSGenerator",
    "Range",
    "SpectrumPlotter",
    "Task",
    "VOTableGenerator",
]
