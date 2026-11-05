from hipster import ColorMap, HTMLGenerator


def test_aladin_lite_url_default(tmp_path):
    HTMLGenerator(root_path=str(tmp_path), aladin_lite_version="3.6.5").generate()

    html = (tmp_path / "index.html").read_text()
    assert "import A from 'https://cdn.jsdelivr.net/npm/aladin-lite@3.6.5/dist/aladin.js';" in html


def test_aladin_lite_url_mirror(tmp_path):
    HTMLGenerator(
        root_path=str(tmp_path),
        aladin_lite_version="3.6.5",
        aladin_lite_url="https://example.org/aladin-lite/{version}/aladin.js",
    ).generate()

    html = (tmp_path / "index.html").read_text()
    assert "import A from 'https://example.org/aladin-lite/3.6.5/aladin.js';" in html


def test_color_map(tmp_path):
    html_generator = HTMLGenerator(root_path=str(tmp_path))
    html_generator.add_votable(
        HTMLGenerator.VOTable(
            url="votable.vot",
            name="Galaxies",
            color="red",
            shape="circle",
            size=5,
            color_map=ColorMap(column="sersic_n_i", vmin=0.2, vmax=10, log=True),
        )
    )
    html_generator.add_catalog(HTMLGenerator.Catalog(url="catalog", name="", color="red", shape="circle", size=5))
    html_generator.generate()

    html = (tmp_path / "index.html").read_text()
    assert "shape: colorMapShape({" in html
    assert '"column": "sersic_n_i"' in html
    assert "Galaxies: sersic_n_i (log)" in html
    assert "shape: 'circle'" in html


def test_without_color_map(tmp_path):
    HTMLGenerator(root_path=str(tmp_path)).generate()

    html = (tmp_path / "index.html").read_text()
    assert "colorMapShape" not in html
    assert "legend" not in html
