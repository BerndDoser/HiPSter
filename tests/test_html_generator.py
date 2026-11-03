from hipster import HTMLGenerator


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
