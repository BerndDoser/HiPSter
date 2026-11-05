import pytest

from hipster import hub


@pytest.mark.parametrize(
    "path, expected",
    [
        ("hf://org/repo/model.onnx", ("model", "org/repo", None, "model.onnx")),
        ("hf://org/repo/a/b/encoder.onnx", ("model", "org/repo", None, "a/b/encoder.onnx")),
        ("hf://org/repo@v1/model.onnx", ("model", "org/repo", "v1", "model.onnx")),
        ("hf://datasets/org/repo", ("dataset", "org/repo", None, "")),
        ("hf://datasets/org/repo/", ("dataset", "org/repo", None, "")),
        ("hf://datasets/org/repo@main/data", ("dataset", "org/repo", "main", "data")),
        ("hf://spaces/org/repo/app.py", ("space", "org/repo", None, "app.py")),
    ],
)
def test_parse_hf_path(path, expected):
    assert hub.parse_hf_path(path) == expected


@pytest.mark.parametrize("path", ["hf://", "hf://org", "hf://datasets/org", "data/org/repo"])
def test_parse_hf_path_invalid(path):
    with pytest.raises(ValueError):
        hub.parse_hf_path(path)


def test_resolve_local_path(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Local paths must not be downloaded")

    monkeypatch.setattr(hub, "hf_hub_download", fail)
    monkeypatch.setattr(hub, "snapshot_download", fail)
    assert hub.resolve_file("tests/models/gaia_decoder.onnx") == "tests/models/gaia_decoder.onnx"
    assert hub.resolve_dataset("data/dataset/") == "data/dataset/"


def test_resolve_file(monkeypatch):
    calls = []

    def hf_hub_download(repo_id, filename, **kwargs):
        calls.append((repo_id, filename, kwargs))
        return f"/cache/{filename}"

    monkeypatch.setattr(hub, "hf_hub_download", hf_hub_download)
    assert hub.resolve_file("hf://org/repo@v1/vae/encoder.onnx") == "/cache/vae/encoder.onnx"
    assert calls == [("org/repo", "vae/encoder.onnx", {"repo_type": "model", "revision": "v1"})]


def test_resolve_file_without_filename():
    with pytest.raises(ValueError):
        hub.resolve_file("hf://org/repo")


def test_resolve_dataset_file(monkeypatch):
    calls = []

    def hf_hub_download(repo_id, filename, **kwargs):
        calls.append((repo_id, filename, kwargs))
        return f"/cache/{filename}"

    monkeypatch.setattr(hub, "hf_hub_download", hf_hub_download)
    assert hub.resolve_dataset("hf://datasets/org/repo/data/train.parquet") == "/cache/data/train.parquet"
    assert calls == [("org/repo", "data/train.parquet", {"repo_type": "dataset", "revision": None})]


@pytest.mark.parametrize("subpath, pattern", [("", "*.parquet"), ("/data", "data/*.parquet")])
def test_resolve_dataset_directory(monkeypatch, tmp_path, subpath, pattern):
    """Only the Parquet files are returned, even if the snapshot contains other files like README.md."""
    (tmp_path / "README.md").write_text("# Dataset card")
    (tmp_path / "data" / "nested").mkdir(parents=True)
    (tmp_path / "data" / "train-00001.parquet").touch()
    (tmp_path / "data" / "nested" / "train-00000.parquet").touch()
    calls = []

    def snapshot_download(repo_id, **kwargs):
        calls.append((repo_id, kwargs))
        return str(tmp_path)

    monkeypatch.setattr(hub, "snapshot_download", snapshot_download)
    files = hub.resolve_dataset(f"hf://datasets/org/repo{subpath}")
    assert files == [
        str(tmp_path / "data" / "nested" / "train-00000.parquet"),
        str(tmp_path / "data" / "train-00001.parquet"),
    ]
    assert calls == [("org/repo", {"repo_type": "dataset", "revision": None, "allow_patterns": pattern})]


def test_resolve_dataset_without_parquet_files(monkeypatch, tmp_path):
    (tmp_path / "README.md").write_text("# Dataset card")
    monkeypatch.setattr(hub, "snapshot_download", lambda repo_id, **kwargs: str(tmp_path))
    with pytest.raises(FileNotFoundError):
        hub.resolve_dataset("hf://datasets/org/repo")
