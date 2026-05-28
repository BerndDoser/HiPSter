import math
import os
from typing import Optional

import healpy
import numpy as np
import pandas as pd
from astropy.io.votable import writeto
from astropy.table import Table
from datasets import load_dataset
from PIL import Image

from hipster.html_generator import HTMLGenerator

from .inference import Inference
from .task import Task


class VOTableGenerator(Task):
    def __init__(
        self,
        encoder: Inference,
        data_path: str,
        data_column: str = "data",
        dataset: str = "illustris",
        output_file: str = "illustris.vot",
        url: str = "http://localhost:8083",
        batch_size: int = 256,
        catalog_name: str = "",
        color: str = "red",
        shape: str = "circle",
        size: int = 10,
        **kwargs,
    ):
        """Generates a catalog of data.

        Args:
            encoder (callable): Function that encodes the data.
            data_path (str): The path to the data.
            data_column (str): The column name of the data.
            dataset (str): The type of dataset. Defaults to "gaia".
            output_file (str, optional): The output file name. Defaults to "votable.xml".
            url (str): The URL of the HiPS server. Defaults to "http://localhost:8083".
            batch_size (int, optional): The batch size to use. Defaults to 256.
            catalog_name (str, optional): The name of the catalog. Defaults to "".
            color (str, optional): The color of the catalog. Defaults to "red".
            shape (str, optional): The shape of the catalog. Defaults to "circle".
            size (int, optional): The size of the catalog. Defaults to 10.
            **kwargs: Additional keyword arguments.
        """
        super().__init__("VOTableGenerator", **kwargs)
        self.encoder = encoder
        self.data_path = data_path
        self.data_column = data_column
        self.dataset = dataset
        self.output_file = output_file
        self.url = url
        self.batch_size = batch_size
        self.catalog_name = catalog_name
        self.color = color
        self.shape = shape
        self.size = size

    def get_catalog(self) -> pd.DataFrame:
        """Generates the catalog."""

        catalog = {
            "preview": [],
            "x": [],
            "y": [],
            "z": [],
            "RA2000": [],
            "DEC2000": [],
        }

        if self.dataset == "gaia":
            catalog["source_id"] = []
        elif self.dataset == "illustris":
            catalog["simulation"] = []
            catalog["snapshot"] = []
            catalog["subhalo_id"] = []

        ds = load_dataset(self.data_path)

        if self.dataset == "gaia":
            ds.map(_generate_gaia_catalog, num_proc=os.cpu_count())
        elif self.dataset == "illustris":
            ds.map(_generate_illustris_catalog, num_proc=os.cpu_count())
        else:
            raise ValueError(f"Unsupported dataset: {self.dataset}")

        for batch in dataset.iter(batch_size=self.batch_size):
            data = np.array(batch[self.data_column]).flatten().reshape(-1, *shape).copy().astype(np.float32)

            if self.dataset == "illustris":
                self.__images_to_jpg(pd.DataFrame(batch), "images")
                self.__images_to_jpg(pd.DataFrame(batch), "thumbnails", size=64)

            latent_position = self.encoder(data)

            angles = np.array(healpy.vec2ang(latent_position)) * 180.0 / math.pi
            angles = angles.T

            if self.dataset == "gaia":
                for source_id in batch["source_id"]:
                    catalog["preview"].append(
                        f"<a href='{self.url}/{self.title}/images/{str(source_id)}.jpg' target='_blank'>"
                        + f"<img src='{self.url}/{self.title}/thumbnails/{str(source_id)}.jpg'></a>"
                    )
                catalog["source_id"].extend(list(batch["source_id"]))
            elif self.dataset == "illustris":
                for simulation, snapshot, subhalo_id in zip(
                    batch["simulation"], batch["snapshot"], batch["subhalo_id"]
                ):
                    catalog["preview"].append(
                        f"<a href='{self.url}/{self.title}/images/{simulation}/{snapshot}/"
                        + f"{str(subhalo_id)}.jpg' target='_blank'>"
                        + f"<img src='{self.url}/{self.title}/thumbnails/{simulation}/{snapshot}/"
                        + f"{str(subhalo_id)}.jpg'></a>"
                    )
                catalog["simulation"].extend(list(batch["simulation"]))
                catalog["snapshot"].extend(list(batch["snapshot"]))
                catalog["subhalo_id"].extend(list(batch["subhalo_id"]))

            catalog["x"].extend(latent_position[:, 0])
            catalog["y"].extend(latent_position[:, 1])
            catalog["z"].extend(latent_position[:, 2])
            catalog["RA2000"].extend(angles[:, 1])
            catalog["DEC2000"].extend(90.0 - angles[:, 0])

        return pd.DataFrame(catalog)

    def __images_to_jpg(self, df: pd.DataFrame, output_path: str, size: Optional[int] = None) -> None:
        """Store images as jpg files."""

        for i in range(len(df)):
            image = np.array(df[self.data_column][i]).reshape(3, 128, 128).transpose(1, 2, 0) * 255
            image = Image.fromarray(image.astype(np.uint8), "RGB")
            if size:
                image = image.resize((size, size))
            os.makedirs(
                os.path.join(
                    self.root_path,
                    output_path,
                    df["simulation"][i],
                    df["snapshot"][i],
                ),
                exist_ok=True,
            )
            image.save(
                os.path.join(
                    self.root_path,
                    output_path,
                    df["simulation"][i],
                    df["snapshot"][i],
                    df["subhalo_id"][i] + ".jpg",
                )
            )

    def execute(self) -> None:
        print(f"Executing task: {self.name}")
        table = Table.from_pandas(self.get_catalog())
        writeto(table, os.path.join(self.root_path, self.output_file))

    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the VOTable to the HTML generator."""
        html_generator.add_votable(
            html_generator.VOTable(
                url=f"{html_generator.url}/{self.output_file}",
                name=self.catalog_name,
                color=self.color,
                shape=self.shape,
                size=self.size,
            )
        )
