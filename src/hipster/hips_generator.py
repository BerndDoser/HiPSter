import math
import multiprocessing as mp
import os

import healpy
import numpy as np
from PIL import Image

# from tqdm.contrib.concurrent import process_map


class HiPSGenerator:

    def __init__(
        self,
        reconstruction: callable,
        image_maker: callable,
        hierarchy: int = 1,
        output_folder: str = "output",
        number_of_workers: int = 1,
    ):
        """Generates a HiPS tiling following the standard defined in
        https://www.ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf

        Args:
            reconstruction (callable): Function that reconstructs the data.
            image_maker (callable): Function that generates the image.
            hierarchy (int, optional): Hierarchy of the HiPS tiling. Defaults to 1.
            output_folder (str, optional): Output folder. Defaults to "output".
            number_of_workers (int, optional): Number of workers. Defaults to 1.
        """

        self.reconstruction = reconstruction
        self.image_maker = image_maker
        self.hierarchy = hierarchy
        self.output_folder = output_folder
        self.number_of_workers = number_of_workers

    def __create_hips_tile(
        self,
        i: int,
        range_j: range,
    ):
        for j in range_j:
            vectors = np.zeros((self.hierarchy**2, 3), dtype=np.float32)
            for sub in range(self.hierarchy**2):
                vectors[sub] = healpy.pix2vec(
                    2**i * self.hierarchy, j * self.hierarchy**2 + sub, nest=True
                )
            recon = self.reconstruction(vectors)
            image = self.generate_tile(recon, i, j, self.hierarchy, 0)
            image = Image.fromarray(image)
            image.save(
                os.path.join(
                    self.output_folder,
                    "Norder" + str(i),
                    "Dir" + str(int(math.floor(j / 10000)) * 10000),
                    "Npix" + str(j) + ".jpg",
                )
            )

    def __create_folders(
        self,
        max_order: int,
    ):
        """Creates all folders and sub-folders to store the HiPS tiles.

        Args:
            max_order (int): Maximum order of the HiPS tiling.
        """
        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)
        for i in range(max_order + 1):
            os.mkdir(os.path.join(self.output_folder, "Norder" + str(i)))
            for j in range(int(math.floor(12 * 4**i / 10000)) + 1):
                os.mkdir(
                    os.path.join(
                        self.output_folder,
                        "Norder" + str(i),
                        "Dir" + str(j * 10000),
                    )
                )

    def generate_tile(self, data, order, pixel, hierarchy, index):
        """Construct the hierarchical tiling of the HiPS."""
        if hierarchy <= 1:
            return self.image_maker(data[index][0])

        q1 = self.generate_tile(data, order + 1, pixel * 4, hierarchy / 2, index * 4)
        q2 = self.generate_tile(
            data, order + 1, pixel * 4 + 1, hierarchy / 2, index * 4 + 1
        )
        q3 = self.generate_tile(
            data, order + 1, pixel * 4 + 2, hierarchy / 2, index * 4 + 2
        )
        q4 = self.generate_tile(
            data, order + 1, pixel * 4 + 3, hierarchy / 2, index * 4 + 3
        )
        result = np.ndarray((q1.shape[0] * 2, q1.shape[1] * 2, 3))
        result[: q1.shape[0], : q1.shape[1]] = q1
        result[q1.shape[0] :, : q1.shape[1]] = q2
        result[: q1.shape[0], q1.shape[1] :] = q3
        result[q1.shape[0] :, q1.shape[1] :] = q4
        return result

    def __call__(
        self,
        max_order: int,
    ):
        """
        Args:
            max_order (int): Maximum order of the HiPS tiling.
        """

        self.__create_folders(max_order)

        for i in range(max_order + 1):
            if self.number_of_workers == 1:
                self.__create_hips_tile(i, range(12 * 4**i))
            else:
                # process_map(_foo, range(0, 30), max_workers=2)

                mypool = []
                for t in range(self.number_of_workers):
                    mypool.append(
                        mp.Process(
                            target=self.__create_hips_tile,
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
