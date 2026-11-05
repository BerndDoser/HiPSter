import numpy as np
import pyarrow.dataset as ds
import pytest

from hipster import ColorMap, Inference, VOTableGenerator


def test_catalog_generator_image(tmp_path):
    VOTableGenerator(
        encoder=Inference("tests/models/illustris_encoder.onnx"),
        data_directory="tests/data/illustris/single-entry.parquet",
        dataset="illustris",
        root_path=tmp_path,
    ).execute()


def test_catalog_generator_spectra():
    votable_generator = VOTableGenerator(
        encoder=Inference("tests/models/gaia_encoder.onnx", input_name="l_x_"),
        data_directory="tests/data/gaia",
        dataset="gaia",
        data_column="flux",
    )

    catalog = votable_generator.get_catalog()

    assert np.allclose(catalog["x"][0], -0.14, atol=1e-2)
    assert np.allclose(catalog["y"][0], 0.01, atol=1e-2)
    assert np.allclose(catalog["z"][0], 0.99, atol=1e-2)


def gaia_votable_generator(**kwargs) -> VOTableGenerator:
    return VOTableGenerator(
        encoder=Inference("tests/models/gaia_encoder.onnx", input_name="l_x_"),
        data_directory="tests/data/gaia",
        dataset="gaia",
        data_column="flux",
        **kwargs,
    )


def test_catalog_extra_columns():
    catalog = gaia_votable_generator(extra_columns=["ra", "source_id"]).get_catalog()

    assert list(catalog.columns) == ["preview", "source_id", "RA2000", "DEC2000", "x", "y", "z", "ra"]
    assert np.array_equal(catalog["ra"], ds.dataset("tests/data/gaia").to_table(columns=["ra"])["ra"].to_numpy())


def test_catalog_extra_column_missing():
    with pytest.raises(ValueError, match="sersic_n_i"):
        gaia_votable_generator(extra_columns=["sersic_n_i"]).get_catalog()


def test_catalog_color_map_column():
    assert gaia_votable_generator(color_map=ColorMap(column="dec", vmin=-90, vmax=90)).extra_columns == ["dec"]
    assert gaia_votable_generator(color_map=ColorMap(column="x", vmin=-1, vmax=1)).extra_columns == []
