import math
import multiprocessing as mp
import os
import pathlib
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from hipster.html_generator import HTMLGenerator

from .create_allsky import create_allsky
from .distortion_correction import correct_distortion
from .task import Task


class NumberedHiPSGenerator(Task):
    def __init__(
        self,
        max_order: int = 1,
        hierarchy: int = 1,
        tile_size: int = 512,
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
            max_order (int, optional): Maximum order of the HiPS tiling. Defaults to 1.
            hierarchy (int, optional): Hierarchy of the HiPS tiling. Defaults to 1.
            image_size (int, optional): Size of the HiPS tiles. Defaults to 512.
            hips_path (str, optional): Output path. Defaults to "output".
            number_of_workers (int, optional): Number of workers. Defaults to 1.
            hips_id (str, optional): HiPS ID. Defaults to "".
            hips_name (str, optional): HiPS name. Defaults to "".
            distortion_correction (bool, optional): Correction of the distortion of the HiPS tiles. Defaults to True.
        """
        super().__init__("DatasetProjection", **kwargs)
        self.max_order = max_order
        self.hierarchy = hierarchy
        self.tile_size = tile_size
        self.image_size = int(tile_size / hierarchy)
        self.hips_path = hips_path
        self.output_path = os.path.join(self.root_path, hips_path)
        self.number_of_workers = number_of_workers
        self.hips_id = hips_id
        self.hips_name = hips_name
        self.distortion_correction = distortion_correction
        self.batch_size = batch_size

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

    def __create_tile_hierachy(self, order, pixel, hierarchy):
        if hierarchy <= 1:
            image = Image.new("RGB", (self.image_size, self.image_size), color=(30, 30, 30))
            draw = ImageDraw.Draw(image)
            text = f"{order},{pixel}"
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=max(12, self.image_size // 6)
            )
            draw.text((self.image_size // 2, self.image_size // 2), text, fill=(255, 255, 255), anchor="mm", font=font)
            image = np.array(image)
            if self.distortion_correction:
                image = correct_distortion(image, order, pixel)
            return image
        q1 = self.__create_tile_hierachy(order + 1, pixel * 4, hierarchy / 2)
        q2 = self.__create_tile_hierachy(order + 1, pixel * 4 + 1, hierarchy / 2)
        q3 = self.__create_tile_hierachy(order + 1, pixel * 4 + 2, hierarchy / 2)
        q4 = self.__create_tile_hierachy(order + 1, pixel * 4 + 3, hierarchy / 2)
        result = np.zeros((q1.shape[0] * 2, q1.shape[1] * 2, 3), dtype=np.uint8)
        result[: q1.shape[0], : q1.shape[1]] = q1
        result[q1.shape[0] :, : q1.shape[1]] = q2
        result[: q1.shape[0], q1.shape[1] :] = q3
        result[q1.shape[0] :, q1.shape[1] :] = q4
        return result

    def __create_tile(self, i, range_j):
        for j in range_j:
            image = self.__create_tile_hierachy(i, j, self.hierarchy)
            image = Image.fromarray(image)
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
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

        for i in range(self.max_order + 1):
            if self.number_of_workers == 1:
                self.__create_tile(i, range(12 * 4**i))
            else:
                mypool = []
                for t in range(self.number_of_workers):
                    mypool.append(
                        mp.Process(
                            target=self.__create_tile,
                            args=(
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
