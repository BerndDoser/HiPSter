# Contributing

Follow this guide if you want to contribute to HiPSter, fix a bug, add a new task or image maker, or
run the test suite locally.

## Set up the development environment

Clone the repository:

```bash
git clone https://github.com/HITS-AIN/HiPSter.git
cd HiPSter
```

uv reads `pyproject.toml` and creates an isolated virtual environment with the exact locked
dependency versions from `uv.lock`:

```bash
uv sync --extra dev
```

This installs HiPSter itself in editable mode plus the `dev` extras (`pytest`, `ruff`, `pre-commit`,
...), so any change you make to the source under `src/hipster/` is picked up immediately.

You don't need to manually activate the virtual environment — prefix commands with `uv run` and uv
takes care of it. If you prefer an activated shell:

```bash
source .venv/bin/activate
```

Install the git hooks so that linting and formatting run on every commit:

```bash
uv run pre-commit install
```

## Run HiPSter locally

The `hipster` CLI is available via `uv run`. The numbering example needs no trained model and is a
quick way to check that everything works:

```bash
uv run hipster --config examples/numbering.yaml
```

## Run the test suite

```bash
uv run --extra dev pytest
```

Run a single test file or test:

```bash
uv run --extra dev pytest tests/test_hips_generator.py
uv run --extra dev pytest tests/test_hips_generator.py::test_hips_generator_image
```

## Lint and format

HiPSter uses [ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

```bash
uv run --extra dev ruff check --no-fix
uv run --extra dev ruff format --check
```

## Add a task or image maker

A new task subclasses {class}`hipster.Task` and implements `execute()`, which writes its output
below `root_path`, and `register()`, which adds its layer to the {class}`hipster.HTMLGenerator`.
An image maker is any callable that turns the model output into an image.

Export new public classes in `__all__` of `src/hipster/__init__.py` and add them to the matching
section of `docs/api.rst`, so that they can be used as `class_path: hipster.<Name>` and appear in the
{doc}`API reference <api>`.

## Build the documentation

The documentation (this site) is built with [Sphinx](https://www.sphinx-doc.org/) from the `docs/`
directory using the `docs` extra:

```bash
uv sync --extra docs
uv run --extra docs sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser to preview it. For live-reloading while editing:

```bash
uv run --extra docs sphinx-autobuild docs docs/_build/html
```

## Pull requests

Open pull requests against `main` of [HITS-AIN/HiPSter](https://github.com/HITS-AIN/HiPSter). CI
runs the ruff checks and the test suite on Python 3.12 and 3.13.
