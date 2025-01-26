#!/usr/bin/env python

import sys

import numpy as np
from astropy.io.votable import writeto
from astropy.table import Table

from hipster import (
    AbsorptionLinePlotter,
    CatalogGenerator,
    HiPSGenerator,
    ImageGenerator,
    Inference,
    SpectrumPlotter,
)


def main() -> int:

    tasks = [
        # "spectrum",
        # "absorption_line",
        "catalog",
        # "images",
    ]
    url = "http://localhost:8083"
    title = "gaia"
    encoder = "tests/models/vae_encoder.onnx"
    decoder = "tests/models/vae_decoder.onnx"
    data_directory = "tests/data/XpSampledMeanSpectrum"
    output_folder = "./HiPSter/" + title
    hips_tile_size = 128
    hierarchy = 4
    max_order = 4

    if "spectrum" in tasks:
        spectrum_plotter = SpectrumPlotter(
            np.arange(336, 1023, 2),
            ylim=(0, 1),
            figsize_in_pixel=hips_tile_size,
            margin=0.02,
            flip=True,
        )
        hips_generator = HiPSGenerator(
            decoder=Inference(decoder),
            image_maker=spectrum_plotter,
            output_folder=output_folder + "/model_spectrum",
            hierarchy=hierarchy,
        )
        hips_generator(max_order=max_order)

    if "absorption_line" in tasks:
        absorption_line_plotter = AbsorptionLinePlotter(
            np.arange(336, 1023, 2),
            figsize_in_pixel=hips_tile_size,
            margin=0.02,
            flip=True,
        )
        hips_generator = HiPSGenerator(
            decoder=Inference(decoder),
            image_maker=absorption_line_plotter,
            output_folder=output_folder + "/model_absorption_line",
            hierarchy=hierarchy,
        )
        hips_generator(max_order=max_order)

    if "catalog" in tasks:
        catalog_generator = CatalogGenerator(
            encoder=Inference(encoder),
            data_directory=data_directory,
            url=url,
            title=title,
        )
        catalog = catalog_generator()
        table = Table.from_pandas(catalog)
        writeto(table, output_folder + "/catalog.vot")

    if "images" in tasks:
        ImageGenerator(
            encoder=Inference(encoder),
            decoder=Inference(decoder),
            data_directory=data_directory,
            output_folder=output_folder + "/images",
        )()

    return 0


if __name__ == "__main__":
    sys.exit(main())
