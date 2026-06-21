import numpy as np

from hipster import Inference, VOTableGenerator


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
