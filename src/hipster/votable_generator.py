import io
import json
import math
import os
from typing import Optional

import healpy
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from astropy.io.votable import writeto
from astropy.table import Table
from PIL import Image

from hipster.html_generator import HTMLGenerator

from .inference import Inference
from .task import Task


class VOTableGenerator(Task):
    def __init__(
        self,
        encoder: Inference,
        data_directory: str,
        data_column: str = "image",
        dataset: str = "illustris",
        output_file: str = "illustris.vot",
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
            data_directory (str): The directory containing the data.
            data_column (str): The column name of the data. Defaults to "image".
            dataset (str): The type of dataset. Defaults to "gaia".
            output_file (str, optional): The output file name. Defaults to "votable.xml".
            batch_size (int, optional): The batch size to use. Defaults to 256.
            catalog_name (str, optional): The name of the catalog. Defaults to "".
            color (str, optional): The color of the catalog. Defaults to "red".
            shape (str, optional): The shape of the catalog. Defaults to "circle".
            size (int, optional): The size of the catalog. Defaults to 10.
            **kwargs: Additional keyword arguments.
        """
        super().__init__("VOTableGenerator", **kwargs)
        self.encoder = encoder
        self.data_directory = data_directory
        self.data_column = data_column
        self.dataset = dataset
        self.output_file = output_file
        self.url = None
        self.batch_size = batch_size
        self.catalog_name = catalog_name
        self.color = color
        self.shape = shape
        self.size = size

    def get_catalog(self) -> pd.DataFrame:
        """Generates the catalog."""

        catalog = {}
        if self.dataset == "gaia":
            catalog["preview"] = []
            catalog["source_id"] = []
            catalog["RA2000"] = []
            catalog["DEC2000"] = []
            catalog["x"] = []
            catalog["y"] = []
            catalog["z"] = []
        elif self.dataset == "illustris":
            catalog["preview"] = []
            catalog["simulation"] = []
            catalog["snapshot"] = []
            catalog["subhalo_id"] = []
            catalog["RA2000"] = []
            catalog["DEC2000"] = []
            catalog["x"] = []
            catalog["y"] = []
            catalog["z"] = []
        elif self.dataset == "celebrities":
            catalog["preview"] = []
            catalog["name"] = []
            catalog["RA2000"] = []
            catalog["DEC2000"] = []
        else:
            raise ValueError(f"Unknown dataset: {self.dataset}")

        dataset = ds.dataset(self.data_directory, format="parquet")

        # If the dataset is Celebrities, we need to load it using the Hugging Face datasets library to get the labels.
        if self.dataset == "celebrities":
            meta = json.loads(pq.read_schema(self.data_directory).metadata[b"huggingface"])
            names = meta["info"]["features"]["label"]["names"]

        # Reshape the data if the shape is stored in the metadata.
        metadata_shape = bytes(self.data_column, "utf8") + b"_shape"
        if dataset.schema.metadata and metadata_shape in dataset.schema.metadata:
            shape_string = dataset.schema.metadata[metadata_shape].decode("utf8")
            shape = shape_string.replace("(", "").replace(")", "").split(",")
            shape = tuple(map(int, shape))

        row_offset = 0
        for batch in dataset.to_batches(batch_size=self.batch_size):
            if self.dataset in ["celebrities", "illustris"]:
                data = batch[self.data_column]
                images = []
                for item in batch[self.data_column]:
                    img_bytes = item["bytes"].as_py()
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((128, 128))
                    images.append(np.array(img))
                data = np.stack(images)
                data = data.transpose(0, 3, 1, 2)
                data = (data / 255.0).astype("float32")
            else:
                data = batch[self.data_column].flatten().to_numpy().reshape(-1, *shape).copy().astype(np.float32)

                # Normalize the data
                for i in range(data.shape[0]):  # batches
                    for j in range(data.shape[1]):  # channels
                        data[i][j] = (data[i][j] - data[i][j].min()) / (data[i][j].max() - data[i][j].min())

            if self.dataset in ["celebrities", "illustris"]:
                self.__generate_images(batch.to_pandas(), "images", offset=row_offset)
                self.__generate_images(batch.to_pandas(), "thumbnails", offset=row_offset, size=64)

            latent_position = self.encoder(data)

            angles = np.array(healpy.vec2ang(latent_position)) * 180.0 / math.pi
            angles = angles.T

            if self.dataset == "gaia":
                for source_id in batch["source_id"]:
                    catalog["preview"].append(
                        f"<a href='{self.url}/{self.title}/images/{str(source_id)}.jpg' target='_blank'>"
                        + f"<img src='{self.url}/{self.title}/thumbnails/{str(source_id)}.jpg'></a>"
                    )
                catalog["source_id"].extend(batch["source_id"].to_pylist())
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
                catalog["simulation"].extend(batch["simulation"].to_pylist())
                catalog["snapshot"].extend(batch["snapshot"].to_pylist())
                catalog["subhalo_id"].extend(batch["subhalo_id"].to_pylist())
            elif self.dataset == "celebrities":
                for i in range(len(batch)):
                    catalog["preview"].append(
                        f"<img src='{self.url}/{self.title}/thumbnails/{str(row_offset + i)}.jpg'>"
                    )
                catalog["name"].extend([names[i] for i in batch["label"].to_pylist()])
                row_offset += len(batch)

            catalog["RA2000"].extend(angles[:, 1])
            catalog["DEC2000"].extend(90.0 - angles[:, 0])
            if self.dataset != "celebrities":
                catalog["x"].extend(latent_position[:, 0])
                catalog["y"].extend(latent_position[:, 1])
                catalog["z"].extend(latent_position[:, 2])

        return pd.DataFrame(catalog)

    def __generate_images(
        self, df: pd.DataFrame, output_path: str, offset: int = 0, size: Optional[int] = None
    ) -> None:
        """Store celebrity images as jpg files."""

        os.makedirs(os.path.join(self.root_path, output_path), exist_ok=True)
        for i in range(len(df)):
            img_bytes = df[self.data_column][i]["bytes"]
            image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            if size:
                image = image.resize((size, size))

            if self.dataset == "illustris":
                os.makedirs(
                    os.path.join(
                        self.root_path,
                        output_path,
                        str(df["simulation"][i]),
                        str(df["snapshot"][i]),
                    ),
                    exist_ok=True,
                )
                image.save(
                    os.path.join(
                        self.root_path,
                        output_path,
                        str(df["simulation"][i]),
                        str(df["snapshot"][i]),
                        str(df["subhalo_id"][i]) + ".jpg",
                    )
                )
            else:
                image.save(
                    os.path.join(
                        self.root_path,
                        output_path,
                        str(offset + i) + ".jpg",
                    )
                )

    def execute(self) -> None:
        print(f"Executing task: {self.name}")
        table = Table.from_pandas(self.get_catalog())
        writeto(table, os.path.join(self.root_path, self.output_file))

    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the VOTable to the HTML generator."""
        self.url = html_generator.url
        html_generator.add_votable(
            html_generator.VOTable(
                url=f"{html_generator.url}/{self.output_file}",
                name=self.catalog_name,
                color=self.color,
                shape=self.shape,
                size=self.size,
            )
        )
