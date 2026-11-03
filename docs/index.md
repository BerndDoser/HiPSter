# HiPSter

HiPSter uses a trained model from [Spherinator](https://github.com/HITS-AIN/Spherinator) with a
spherical latent space to create HiPS tilings and a catalog that can be visualized interactively on
the surface of a sphere using [Aladin Lite](https://github.com/cds-astro/aladin-lite).

```{figure} assets/P404_f2.png
---
name: fig:latent_space
width: 300px
align: center
---
```

Spherinator and HiPSter are tools that provide explorative access and visualization for multimodal
data from extremely large astrophysical datasets, ranging from exascale cosmological simulations to
multi-billion object observational galaxy surveys. Training data for both is produced with
[PEST](https://github.com/HITS-AIN/PEST) ([documentation](https://pest.readthedocs.io/en/latest/)).

## Citation

If you use HiPSter in your research, please cite {cite}`Polsterer2024`.

```{bibliography}
```

```{toctree}
:caption: Getting started
:maxdepth: 2
:hidden:

install
```

```{toctree}
:caption: User guide
:maxdepth: 2
:hidden:

configuration
tasks
visualization
```

```{toctree}
:caption: Reference
:maxdepth: 2
:hidden:

api
```

```{toctree}
:caption: Development
:maxdepth: 2
:hidden:

contributing
```
