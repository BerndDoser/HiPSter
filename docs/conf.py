"""Sphinx configuration."""

from datetime import UTC, datetime

project = "HiPSter"
copyright = f"{datetime.now(tz=UTC).year}, HITS gGmbH"
author = """Kai Polsterer <kai.polsterer@h-its.org>,
            Bernd Doser <bernd.doser@h-its.org>,
            Andreas Fehlner <andreas.fehlner@h-its.org>,
            Sebastian T. Gomez <sebastian.trujillogomez@h-its.org>"""

extensions = [
    "myst_parser",
    "sphinxcontrib.bibtex",
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

bibtex_bibfiles = ["references.bib"]
html_theme = "sphinx_rtd_theme"
templates_path = ["_templates"]

# HiPSter documents constructor arguments in __init__ docstrings
autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
