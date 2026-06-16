import math
from pathlib import Path

import numpy
from PIL import Image


def create_allsky(
    data_directory: Path,
    order: int,
    edge_width: int = 64,
):
    """Creates an all-sky image by stitching together the individual HEALPix tiles.

    Args:
        data_directory (Path): The directory containing the HEALPix tiles.
        order (int): The HEALPix order of the tiles.
        edge_width (int, optional): The width of each tile in pixels. Defaults to 64.
    """
    width = math.floor(math.sqrt(12 * 4**order))
    height = math.ceil(12 * 4**order / width)
    result = numpy.zeros((edge_width * height, edge_width * width, 3))

    for i in range(12 * 4**order):
        file = data_directory / Path("Norder" + str(order)) / Path("Dir0") / Path("Npix" + str(i) + ".jpg")
        if not file.exists():
            raise RuntimeError("File not found: " + str(file))

        image = numpy.array(Image.open(file).convert("RGB").resize((edge_width, edge_width), Image.LANCZOS)) / 255.0

        x = i % width
        y = math.floor(i / width)
        result[
            y * edge_width : (y + 1) * edge_width,
            x * edge_width : (x + 1) * edge_width,
        ] = image
    image = Image.fromarray((numpy.clip(result, 0, 1) * 255).astype(numpy.uint8), mode="RGB")
    image.save(data_directory / Path("Norder" + str(order)) / Path("Allsky.jpg"))
