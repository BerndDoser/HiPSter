import pyarrow.parquet as pq
import pytest

from hipster import HiPSCatalogGenerator, HTMLGenerator, Inference


def gaia_hips_catalog_generator(tmp_path, **kwargs) -> HiPSCatalogGenerator:
    return HiPSCatalogGenerator(
        encoder=Inference("tests/models/gaia_encoder.onnx", input_name="l_x_"),
        data_directory="tests/data/gaia",
        dataset="gaia",
        data_column="flux",
        root_path=str(tmp_path),
        catalog_name="Gaia",
        level_limit=4,
        cluster={"mode": "local", "n_workers": 1, "threads_per_worker": 1, "memory_per_worker": "2GB"},
        **kwargs,
    )


def test_encode_shards(tmp_path):
    for shard_index in range(2):
        gaia_hips_catalog_generator(
            tmp_path, stage="encode", num_shards=2, shard_index=shard_index, extra_columns=["ra"]
        ).execute()

    assert len(list((tmp_path / "catalog_parquet").glob("part-*.parquet"))) == 2
    table = pq.read_table(tmp_path / "catalog_parquet")
    assert table.num_rows == 46
    assert {"source_id", "RA2000", "DEC2000", "x", "y", "z", "ra", "score"} <= set(table.column_names)


def test_parquet_path_inside_hips_catalog(tmp_path):
    with pytest.raises(ValueError, match="parquet_path"):
        gaia_hips_catalog_generator(tmp_path, parquet_path=str(tmp_path / "catalog" / "parquet"))


def test_density_up_to_depth(tmp_path):
    assert gaia_hips_catalog_generator(tmp_path).algorithm["density_up_to_depth"] == 3
    with pytest.raises(ValueError, match="density_up_to_depth"):
        gaia_hips_catalog_generator(tmp_path, algorithm={"density_up_to_depth": 4})


def test_register(tmp_path):
    html_generator = HTMLGenerator(root_path=str(tmp_path), url="https://example.org/hipster")
    gaia_hips_catalog_generator(tmp_path).register(html_generator)
    html_generator.generate()

    assert "A.catalogHiPS('https://example.org/hipster/catalog'" in (tmp_path / "index.html").read_text()


def test_build(tmp_path):
    pytest.importorskip("hipscatalog_gen")

    hips_catalog_generator = gaia_hips_catalog_generator(tmp_path)
    hips_catalog_generator.register(HTMLGenerator(root_path=str(tmp_path), url="https://example.org/hipster"))
    hips_catalog_generator.execute()

    output = tmp_path / "catalog"
    for file in ["Norder1/Allsky.tsv", "Norder2/Allsky.tsv", "metadata.xml", "Moc.fits"]:
        assert (output / file).exists()

    properties = (output / "properties").read_text()
    assert "hips_service_url  = https://example.org/hipster/catalog\n" in properties
    assert "creator_did       = ivo://example.org/hipster/catalog\n" in properties

    # Each tile starts with a completeness comment and a header line, each object is stored exactly once.
    rows = [line for tile in output.glob("Norder*/Dir*/Npix*.tsv") for line in tile.read_text().splitlines()[2:]]
    assert len(rows) == 46
