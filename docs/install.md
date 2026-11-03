# Installation

Install the published package, [`astro-hipster`](https://pypi.org/project/astro-hipster/), from PyPI.
HiPSter requires Python 3.12 or newer.

## Using pip

We recommend installing into a virtual environment rather than system-wide:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install astro-hipster
```

## Using uv

If you have [uv](https://docs.astral.sh/uv/) installed, it manages the virtual environment for you:

```bash
uv venv
source .venv/bin/activate

uv pip install astro-hipster
```

## GPU support

Model inference runs on [ONNX Runtime](https://onnxruntime.ai/). To run it on an NVIDIA GPU, install
the `cuda` extra:

```bash
pip install "astro-hipster[cuda]"
```

## HiPS catalogs

The {class}`~hipster.HiPSCatalogGenerator` builds its catalog tiles with
[hipscatalog_gen](https://github.com/linea-it/hipscatalog_gen), which is installed with the
`catalog` extra:

```bash
pip install "astro-hipster[catalog]"
```

## Verify the installation

```bash
hipster --version
hipster --help
```

This should print the installed version and the command-line usage. You're now ready to
{doc}`write a configuration file <configuration>` and generate your first HiPS tiling.

To work on HiPSter itself, see {doc}`contributing`.
