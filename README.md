[![Build Status](https://github.com/HITS-AIN/hipster/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/HITS-AIN/hipster/actions/workflows/python-package.yml?branch=main)
[![Documentation Status](https://readthedocs.org/projects/spherinator/badge/?version=latest)](https://spherinator.readthedocs.io/en/latest/?badge=latest)
![versions](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)

# HiPSter

[Spherinator](https://github.com/HITS-AIN/Spherinator) and
[HiPSter](https://github.com/HITS-AIN/HiPSter) are tools that provide explorative access
and visualization for multimodal data from extremely large astrophysical datasets, ranging from
exascale cosmological simulations to multi-billion object observational galaxy surveys.

HiPSter uses a trained model from Spherinator with a spherical latent space to create HiPS tilings
and a catalog that can be visualized interactively on the surface of a sphere using
[Aladin Lite](https://github.com/cds-astro/aladin-lite).


<p align="center">
  <img src="images/P404_f2.png" width="400" height="400">
</p>


## Installation

```bash
pip install astro-hipster
```

## Usage

The `HiPSter` package provides a CLI to create HiPS tilings and a catalog from the spherical latent
space representation.

```bash
hipster --config <path_to_config_file>
```

For more details run `hipster --help` or check the [documentation](https://spherinator.readthedocs.io/en/latest/hipster.html#command-line-interface).


## Documentation

The `HiPSter` documentation is part of the Spherinator documentation and can be found at:

[Read The Docs](https://spherinator.readthedocs.io/en/latest/hipster.html)


## Acknowledgments

Funded by the European Union. This work has received funding from the European High-Performance Computing Joint Undertaking (JU) and Belgium, Czech Republic, France, Germany, Greece, Italy, Norway, and Spain under grant agreement No 101093441.

Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European High Performance Computing Joint Undertaking (JU) and Belgium, Czech Republic, France, Germany, Greece, Italy, Norway, and Spain. Neither the European Union nor the granting authority can be held responsible for them.


## License

This project is licensed under the [Apache-2.0 License](http://www.apache.org/licenses/LICENSE-2.0).


## Citation

If you use HiPSter in your research, we provide a [citation](./CITATION.cff) to use:

```bibtex
@article{Polsterer_Spherinator_and_HiPSter_2024,
author = {Polsterer, Kai Lars and Doser, Bernd and Fehlner, Andreas and Trujillo-Gomez, Sebastian},
title = {{Spherinator and HiPSter: Representation Learning for Unbiased Knowledge Discovery from Simulations}},
url = {https://arxiv.org/abs/2406.03810},
doi = {10.48550/arXiv.2406.03810},
year = {2024}
}
```
