"""Resolves Hugging Face paths (hf://...) to local files in the Hugging Face cache.

Models are given as ``hf://<namespace>/<name>[@<revision>]/<path>`` and datasets as
``hf://datasets/<namespace>/<name>[@<revision>][/<path>]``, following the convention of
``huggingface_hub.HfFileSystem``. All other paths are returned unchanged.
"""

import glob
import os

from huggingface_hub import hf_hub_download, snapshot_download

HF_PREFIX = "hf://"
_REPO_TYPES = {"datasets": "dataset", "spaces": "space"}


def is_hf_path(path: str | os.PathLike) -> bool:
    """Returns True if the path refers to a Hugging Face repository."""
    return os.fspath(path).startswith(HF_PREFIX)


def parse_hf_path(path: str) -> tuple[str, str, str | None, str]:
    """Splits a Hugging Face path into repository type, repository id, revision and path in the repository.

    Args:
        path (str): Path of the form ``hf://[datasets/|spaces/]<namespace>/<name>[@<revision>][/<path>]``.

    Returns:
        tuple: (repo_type, repo_id, revision, path_in_repo), where revision is None if not given.
    """
    if not is_hf_path(path):
        raise ValueError(f"Not a Hugging Face path: {path}")
    parts = [part for part in path[len(HF_PREFIX) :].split("/") if part]
    repo_type = _REPO_TYPES.get(parts[0], "model") if parts else "model"
    if parts and parts[0] in _REPO_TYPES:
        parts = parts[1:]
    if len(parts) < 2:
        raise ValueError(
            f"Invalid Hugging Face path: {path}, expected hf://[datasets/]<namespace>/<name>[@<revision>]/<path>"
        )
    namespace, name, *rest = parts
    name, _, revision = name.partition("@")
    return repo_type, f"{namespace}/{name}", revision or None, "/".join(rest)


def resolve_file(path: str | os.PathLike) -> str:
    """Returns the local path of a file, downloading Hugging Face files into the Hugging Face cache."""
    path = os.fspath(path)
    if not is_hf_path(path):
        return path
    repo_type, repo_id, revision, filename = parse_hf_path(path)
    if not filename:
        raise ValueError(f"Hugging Face path {path} must point to a file")
    return hf_hub_download(repo_id, filename, repo_type=repo_type, revision=revision)


def resolve_dataset(path: str | os.PathLike) -> str | list[str]:
    """Returns the local Parquet dataset, downloading Hugging Face datasets into the Hugging Face cache.

    For a Hugging Face repository or directory, only the Parquet files are downloaded and returned as a sorted
    list, so that other files of the repository (e.g. README.md) are not read as part of the dataset.
    """
    path = os.fspath(path)
    if not is_hf_path(path):
        return path
    repo_type, repo_id, revision, subpath = parse_hf_path(path)
    if subpath.endswith(".parquet"):
        return hf_hub_download(repo_id, subpath, repo_type=repo_type, revision=revision)

    prefix = f"{subpath}/" if subpath else ""
    local_path = snapshot_download(repo_id, repo_type=repo_type, revision=revision, allow_patterns=f"{prefix}*.parquet")
    files = sorted(glob.glob(os.path.join(local_path, subpath, "**", "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No Parquet files found in {path}")
    return files
