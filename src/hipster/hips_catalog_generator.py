import glob
import json
import os
import warnings
from typing import Literal
from urllib.parse import urlparse

import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from hipster.html_generator import HTMLGenerator

from .inference import Inference
from .votable_generator import VOTableGenerator


class HiPSCatalogGenerator(VOTableGenerator):
    def __init__(
        self,
        encoder: Inference,
        data_directory: str,
        hips_path: str = "catalog",
        parquet_path: str | None = None,
        score: str | None = None,
        order_desc: bool = False,
        level_limit: int = 11,
        selection_mode: Literal["score_density_hybrid", "score_global"] = "score_density_hybrid",
        algorithm: dict | None = None,
        cluster: dict | None = None,
        stage: Literal["all", "encode", "build"] = "all",
        num_shards: int = 1,
        shard_index: int = 0,
        **kwargs,
    ):
        """Generates a progressive HiPS catalog following the standard defined in
        https://www.ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf

        The catalog is streamed batch-wise into Parquet files, which are then converted into HiPS catalog tiles
        using hipscatalog_gen (https://github.com/linea-it/hipscatalog_gen), running on Dask locally or on Slurm.

        Args:
            encoder (Inference): Function that encodes the data.
            data_directory (str): The directory containing the data.
            hips_path (str, optional): Output path of the HiPS catalog below root_path. Defaults to "catalog".
            parquet_path (str, optional): Output path of the encoded Parquet catalog.
                Defaults to "<root_path>/<hips_path>_parquet".
            score (str, optional): Column name or expression defining which objects are shown at low orders.
                Defaults to None, which uses a uniform random score.
            order_desc (bool, optional): Show objects with the highest score first. Defaults to False.
            level_limit (int, optional): Maximal HiPS order of the catalog (4-11). Defaults to 11.
            selection_mode (str, optional): Selection mode of hipscatalog_gen. Defaults to "score_density_hybrid".
            algorithm (dict, optional): Additional options of the hipscatalog_gen selection mode. Defaults to None.
            cluster (dict, optional): Dask cluster options of hipscatalog_gen (local or slurm). Defaults to None.
            stage (str, optional): Run only the "encode" or the "build" stage. Defaults to "all".
            num_shards (int, optional): Number of shards to split the encoding into. Defaults to 1.
            shard_index (int, optional): Shard to encode, used e.g. for Slurm array jobs. Defaults to 0.
            **kwargs: Additional keyword arguments passed to VOTableGenerator.
        """
        super().__init__(encoder, data_directory, **kwargs)
        self.name = "HiPSCatalogGenerator"
        self.hips_path = hips_path
        self.output_path = os.path.join(self.root_path, hips_path)
        self.parquet_path = parquet_path or os.path.join(self.root_path, f"{hips_path}_parquet")
        self.score = score
        self.order_desc = order_desc
        self.level_limit = level_limit
        self.selection_mode = selection_mode
        self.algorithm = dict(algorithm or {})
        self.cluster = cluster or {"mode": "local", "n_workers": 4, "threads_per_worker": 1, "memory_per_worker": "4GB"}
        self.stage = stage
        self.num_shards = num_shards
        self.shard_index = shard_index

        if not 4 <= level_limit <= 11:
            raise ValueError(f"level_limit must be between 4 and 11, got {level_limit}")
        if not 0 <= shard_index < num_shards:
            raise ValueError(f"shard_index must be between 0 and {num_shards - 1}, got {shard_index}")
        if selection_mode == "score_density_hybrid":
            # Only the orders above density_up_to_depth take all remaining objects, otherwise objects are dropped.
            self.algorithm.setdefault("density_up_to_depth", min(4, level_limit - 1))
            if self.algorithm["density_up_to_depth"] >= level_limit:
                raise ValueError("algorithm.density_up_to_depth must be smaller than level_limit")
        if num_shards > 1 and self.dataset in ["celebrities", "emoji"]:
            raise ValueError(f"Sharding is not supported for dataset {self.dataset}")
        output_path = os.path.abspath(self.output_path)
        if os.path.commonpath([output_path, os.path.abspath(self.parquet_path)]) == output_path:
            raise ValueError("parquet_path must not be inside the HiPS catalog, which is overwritten")

    def _open_dataset(self) -> ds.Dataset:
        """Opens the files of the input dataset belonging to this shard."""
        dataset = super()._open_dataset()
        if self.num_shards == 1:
            return dataset
        files = sorted(dataset.files)[self.shard_index :: self.num_shards]
        return ds.dataset(files, schema=dataset.schema, format="parquet")

    def __encode(self) -> None:
        """Encodes the data and writes the catalog batch-wise into a Parquet file."""
        os.makedirs(self.parquet_path, exist_ok=True)
        if self.num_shards == 1:
            for file in glob.glob(os.path.join(self.parquet_path, "part-*.parquet")):
                os.remove(file)

        rng = np.random.default_rng(self.shard_index)
        writer = None
        try:
            for df in self.iter_catalog():
                if self.score is None:
                    df["score"] = rng.random(len(df))
                table = pa.Table.from_pandas(df, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(
                        os.path.join(self.parquet_path, f"part-{self.shard_index:05d}.parquet"), table.schema
                    )
                writer.write_table(table.cast(writer.schema))
        finally:
            if writer is not None:
                writer.close()

    def __creator_did(self) -> str:
        """Returns the IVOA identifier of the HiPS catalog."""
        url = urlparse(self.url or "")
        authority = url.hostname or "PRIVATE_USER"
        return f"ivo://{authority}{url.path.rstrip('/')}/{self.hips_path}"

    def __build(self) -> None:
        """Builds the HiPS catalog tiles from the Parquet catalog."""
        try:
            from hipscatalog_gen import run_pipeline
            from hipscatalog_gen.config import load_config_from_dict
        except ImportError as e:
            raise ImportError(
                "HiPSCatalogGenerator requires hipscatalog-gen: pip install 'astro-hipster[catalog]'"
            ) from e

        name = self.catalog_name or self.title or self.hips_path
        config = {
            "input": {"paths": [os.path.join(self.parquet_path, "*.parquet")], "format": "parquet"},
            "columns": {"ra": "RA2000", "dec": "DEC2000"},
            "algorithm": {
                "selection_mode": self.selection_mode,
                "level_limit": self.level_limit,
                self.selection_mode: {
                    "score_column": self.score or "score",
                    "order_desc": self.order_desc,
                    **self.algorithm,
                },
            },
            "cluster": self.cluster,
            "output": {
                "out_dir": self.output_path,
                "cat_name": name,
                "obs_title": name,
                "creator_did": self.__creator_did(),
                "overwrite": True,
            },
        }
        run_pipeline(load_config_from_dict(config))
        self.__check_completeness()
        self.__patch_properties()

    def __check_completeness(self) -> None:
        """Warns if not all objects were written into the HiPS catalog."""
        with open(os.path.join(self.output_path, "telemetry.json"), encoding="utf-8") as f:
            counts = json.load(f).get("output_counts", {})
        num_input = counts.get("input", {}).get("total")
        num_output = counts.get("output", {}).get("total")
        if num_input != num_output:
            warnings.warn(f"HiPS catalog contains {num_output} of {num_input} objects", stacklevel=2)

    def __patch_properties(self) -> None:
        """Sets the public service URL and adds the creator_did required by the HiPS standard."""
        updates = {"creator_did": self.__creator_did()}
        if self.url:
            updates["hips_service_url"] = f"{self.url}/{self.hips_path}"

        properties = os.path.join(self.output_path, "properties")
        with open(properties, encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            key = line.split("=")[0].strip()
            if key in updates:
                lines[i] = f"{key:<17} = {updates.pop(key)}\n"
        first_entry = next((i for i, line in enumerate(lines) if not line.startswith("#")), len(lines))
        lines[first_entry:first_entry] = [f"{key:<17} = {value}\n" for key, value in updates.items()]
        with open(properties, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def execute(self) -> None:
        print(f"Executing task: {self.name}")
        if self.stage in ["all", "encode"]:
            self.__encode()
        if self.stage in ["all", "build"]:
            self.__build()

    def register(self, html_generator: HTMLGenerator) -> None:
        """Register the HiPS catalog to the HTML generator."""
        self.url = html_generator.url
        html_generator.add_catalog(
            html_generator.Catalog(
                url=f"{html_generator.url}/{self.hips_path}",
                name=self.catalog_name,
                color=self.color,
                shape=self.shape,
                size=self.size,
                color_map=self.color_map,
            )
        )
