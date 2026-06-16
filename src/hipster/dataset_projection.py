import io
import math
import multiprocessing as mp
import os
import pathlib
from datetime import datetime, timezone
from typing import Callable

import healpy
import numpy as np
import pyarrow.dataset as ds
from PIL import Image

from hipster.html_generator import HTMLGenerator

from .create_allsky import create_allsky
from .distortion_correction import correct_distortion
from .inference import Inference
from .task import Task


class DatasetProjection(Task):
    def __init__(
        self,
        encoder: Inference,
        image_maker: Callable,
        data_directory: str,
        data_column: str = "image",
        max_order: int = 1,
        hierarchy: int = 1,
        tile_size: int = 512,
        model_input_size: int = 128,
        hips_path: str = "output",
        number_of_workers: int = 1,
        hips_id: str = "",
        hips_name: str = "",
        distortion_correction: bool = True,
        batch_size: int = 256,
        **kwargs,
    ):
        """Generates a HiPS tiling following the standard defined in
        https://www.ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf

        Args:
            encoder(Inference): Function that encodes the data.
            data_directory (str): The directory containing the data.
            image_maker (callable): Function that generates the image.
            max_order (int, optional): Maximum order of the HiPS tiling. Defaults to 1.
            hierarchy (int, optional): Hierarchy of the HiPS tiling. Defaults to 1.
            tile_size (int, optional): Size of the HiPS tiles. Defaults to 512.
            output_path (str, optional): Output path. Defaults to "output".
            number_of_workers (int, optional): Number of workers. Defaults to 1.
            hips_id (str, optional): HiPS ID. Defaults to "".
            hips_name (str, optional): HiPS name. Defaults to "".
            distortion_correction (bool, optional): Correction of the distortion of the HiPS tiles. Defaults to True.
        """
        super().__init__("DatasetProjection", **kwargs)
        self.encoder = encoder
        self.image_maker = image_maker
        self.data_column = data_column
        self.tile_size = tile_size
        self.model_input_size = model_input_size
        self.image_size = int(tile_size / hierarchy)
        self.hierarchy = hierarchy
        self.hips_path = hips_path
        self.output_path = os.path.join(self.root_path, hips_path)
        self.number_of_workers = number_of_workers
        self.max_order = max_order
        self.hips_id = hips_id
        self.hips_name = hips_name
        self.distortion_correction = distortion_correction
        self.batch_size = batch_size

        dataset = ds.dataset(data_directory, format="parquet")
        table = dataset.to_table(columns=[self.data_column])
        self.num_rows = table.num_rows
        self.images = table[self.data_column]

        self.catalog = None

    def __create_folders(
        self,
        max_order: int,
    ):
        """Creates all folders and sub-folders to store the HiPS tiles.

        Args:
            max_order (int): Maximum order of the HiPS tiling.
        """
        path1 = pathlib.Path(self.output_path)
        path1.mkdir(parents=True, exist_ok=True)
        for i in range(max_order + 1):
            path2 = path1 / f"Norder{i}"
            path2.mkdir(parents=True, exist_ok=True)
            for j in range(int(math.floor(12 * 4**i / 10000)) + 1):
                path3 = path2 / f"Dir{j * 10000}"
                path3.mkdir(parents=True, exist_ok=True)

    def __write_properties(self) -> None:
        """Writes the properties of the HiPS data to a file."""
        with open(os.path.join(self.output_path, "properties"), "w", encoding="utf-8") as f:
            f.write(f"""
creator_did          = ivo://HITS/hipster
obs_title            = {self.hips_name}
dataproduct_type     = image
dataproduct_subtype  = color
hips_version         = 1.4
hips_creation_date   = {datetime.now(tz=timezone.utc).isoformat()}
hips_status          = public master clonable
hips_tile_format     = jpeg
hips_order           = {self.max_order}
hips_order_min       = 0
hips_tile_width      = {self.tile_size}
hips_frame           = equatorial
""")

    def __calculate_healpix_cells(
        self,
        numbers: range,
        order: int,
        pixels: range,
    ):
        healpix_cells = {}  # create an extra map to quickly find images in a cell
        for pixel in pixels:
            healpix_cells[pixel] = []  # create empty lists for each cell
        for number in numbers:
            pixel = healpy.vec2pix(
                2**order,
                self.catalog[number][0],
                self.catalog[number][1],
                self.catalog[number][2],
                nest=True,
            )
            if pixel in healpix_cells:
                healpix_cells[pixel].append(int(number))
        return healpix_cells

    def __embed_tile(self, order, pixel, hierarchy, idx):
        if hierarchy <= 1:
            if len(idx) == 0:
                data = np.ones((3, self.image_size, self.image_size))
                data[0] = data[0] * 77.0 / 255.0  # deep purple
                data[1] = data[1] * 0.0 / 255.0
                data[2] = data[2] * 153.0 / 255.0
                # data = np.swapaxes(data, 0, 2)
                image = self.image_maker(data)
            else:
                vector = healpy.pix2vec(2**order, pixel, nest=True)
                distances = np.sum(np.square(self.catalog[np.array(idx)] - vector), axis=1)
                best = idx[np.argmin(distances)]
                data = self.images[best].as_py()["bytes"]
                img = Image.open(io.BytesIO(data)).resize((self.image_size, self.image_size))
                data = np.array(img.convert("RGB")) / 255.0  # (H, W, 3)
                image = self.image_maker(data.transpose(2, 0, 1))  # expects (C, H, W)
                if self.distortion_correction:
                    image = correct_distortion(image, order, pixel)
            return image
        healpix_cells = self.__calculate_healpix_cells(idx, order + 1, range(pixel * 4, pixel * 4 + 4))
        q1 = self.__embed_tile(order + 1, pixel * 4, hierarchy / 2, healpix_cells[pixel * 4])
        q2 = self.__embed_tile(order + 1, pixel * 4 + 1, hierarchy / 2, healpix_cells[pixel * 4 + 1])
        q3 = self.__embed_tile(order + 1, pixel * 4 + 2, hierarchy / 2, healpix_cells[pixel * 4 + 2])
        q4 = self.__embed_tile(order + 1, pixel * 4 + 3, hierarchy / 2, healpix_cells[pixel * 4 + 3])
        result = np.zeros((q1.shape[0] * 2, q1.shape[1] * 2, 3), dtype=np.uint8)
        result[: q1.shape[0], : q1.shape[1]] = q1
        result[q1.shape[0] :, : q1.shape[1]] = q2
        result[: q1.shape[0], q1.shape[1] :] = q3
        result[q1.shape[0] :, q1.shape[1] :] = q4
        return result

    def __create_embeded_tile(self, healpix_cells, i, range_j):
        for j in range_j:
            image = self.__embed_tile(i, j, self.hierarchy, healpix_cells[j])
            image = Image.fromarray(image)
            image.save(
                os.path.join(
                    self.output_path,
                    "Norder" + str(i),
                    "Dir" + str(int(math.floor(j / 10000)) * 10000),
                    "Npix" + str(j) + ".jpg",
                )
            )

    def execute(self) -> None:
        """Generates the HiPS tiles."""

        print(f"Executing task: {self.name}")
        self.__create_folders(self.max_order)

        if self.catalog is None:
            print("Calculating catalog...")
            self.catalog = []
            for batch in ds.dataset.to_batches(batch_size=self.batch_size):
                data = batch[self.data_column]
                images = []
                for item in batch[self.data_column]:
                    img_bytes = item["bytes"].as_py()
                    img = (
                        Image.open(io.BytesIO(img_bytes))
                        .convert("RGB")
                        .resize((self.model_input_size, self.model_input_size))
                    )
                    images.append(np.array(img))
                data = np.stack(images)  # (N, 128, 128, 3)
                data = data.transpose(0, 3, 1, 2)  # (N, 3, 128, 128)
                data = (data / 255.0).astype("float32")  # Normalize to [0, 1]
                z = self.encoder(data)
                self.catalog.append(z)
            self.catalog = np.concatenate(self.catalog, axis=0)  # (num_rows, 3)

        for i in range(self.max_order + 1):
            healpix_cells = self.__calculate_healpix_cells(range(self.num_rows), i, range(12 * 4**i))

            if self.number_of_workers == 1:
                self.__create_embeded_tile(healpix_cells, i, range(12 * 4**i))
            else:
                # process_map(_foo, range(0, 30), max_workers=2)

                mypool = []
                for t in range(self.number_of_workers):
                    mypool.append(
                        mp.Process(
                            target=self.__create_embeded_tile,
                            args=(
                                healpix_cells,
                                i,
                                range(
                                    t * 12 * 4**i // self.number_of_workers,
                                    (t + 1) * 12 * 4**i // self.number_of_workers,
                                ),
                            ),
                        )
                    )
                    mypool[-1].start()
                for process in mypool:
                    process.join()

            create_allsky(data_directory=pathlib.Path(self.output_path), order=i)

        # Write the properties of the HiPS data to a file
        # This must be done after the tiles are generated
        # to ensure the tile size is correct
        self.__write_properties()

    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the HiPS generator to the HTML generator."""
        html_generator.add_image_layer(
            html_generator.ImageLayer(
                hips_id=self.hips_id,
                hips_name=self.hips_name,
                hips_url=f"{html_generator.url}/{self.hips_path}",
                hips_max_order=self.max_order,
            )
        )
