# Tasks

Each entry in the `tasks` list of the {doc}`configuration file <configuration>` creates one layer of
the generated Aladin Lite page: a HiPS tiling or a catalog.

## HiPS tilings

HiPSter uses the HEALPix framework to generate a Hierarchical Progressive Survey (HiPS) for the
corresponding spherical latent space positions. The HiPS representation can be visualized with
[Aladin Lite](https://github.com/cds-astro/aladin-lite).

```{figure} assets/HEALPix.png
---
name: fig:healpix
width: 500px
align: center
---
Source: {cite}`Fernique_2015`
```

The tiling tasks share these parameters:

- `max_order`: the deepest HiPS order to generate.
- `hierarchy`: the number of sub-cells per tile edge.
- `distortion_correction`: compensates the distortion of the HEALPix cells.
- `hips_id`, `hips_name`, `hips_path`: identifier and display name of the layer, and its output
  directory below `root_path`.

## Available tasks

| Class | Purpose |
|---|---|
| {class}`~hipster.HiPSGenerator` | Decodes the HEALPix cell centers with the model's decoder and renders the reconstructions as HiPS tiles. |
| {class}`~hipster.DatasetProjection` | Encodes a dataset with the model's encoder and places the real images at their latent space positions as HiPS tiles. |
| {class}`~hipster.VOTableGenerator` | Encodes a dataset and writes a VOTable catalog with the latent space positions, shown as an overlay in Aladin Lite. |
| {class}`~hipster.HiPSCatalogGenerator` | Like the VOTableGenerator, but writes a progressive HiPS catalog for large datasets, see {ref}`hips-catalogs`. |
| {class}`~hipster.NumberedHiPSGenerator` | Labels each HiPS tile with its order and pixel number, useful to check the tiling. No model required. |

(hips-catalogs)=

## HiPS catalogs

A VOTable catalog is a single file that Aladin Lite loads completely, which is too slow for large
datasets. The {class}`~hipster.HiPSCatalogGenerator` writes a progressive
[HiPS catalog](https://www.ivoa.net/documents/HiPS/20170519/REC-HIPS-1.0-20170519.pdf) instead:
the objects are split into tiles per HiPS order, and Aladin Lite only loads the tiles in view.
It needs the {doc}`catalog extra <install>` and accepts the same parameters as the
VOTableGenerator, plus:

- `hips_path`: output directory of the HiPS catalog below `root_path`. Defaults to `catalog`.
- `level_limit`: the deepest HiPS order of the catalog (4–11). Defaults to 11.
- `score`: column or expression that decides which objects are shown at low orders, with
  `order_desc` to show the highest score first. Defaults to a uniform random score.
- `cluster`: the Dask cluster that builds the tiles, `mode: local` or `mode: slurm`.

```yaml
- class_path: hipster.HiPSCatalogGenerator
  init_args:
    encoder:
      model_path: encoder.onnx
    data_directory: data/gaia/xp_calibrated
    catalog_name: Gaia XP DR3 HiPS catalog
    hips_path: gaia/catalog
    color: orange
    shape: circle
    size: 10
    cluster:
      mode: local
      n_workers: 8
      memory_per_worker: 8GB
```

The task runs in two stages: `encode` streams the encoded catalog batch-wise into Parquet files
(`parquet_path`, by default `<hips_path>_parquet` next to the catalog), and `build` turns them into
HiPS tiles with [hipscatalog_gen](https://github.com/linea-it/hipscatalog_gen). By default
(`stage: all`) both run one after the other.

For large datasets, split the encoding into `num_shards` shards that run in parallel, e.g. as a
Slurm array job, and build the catalog afterwards in a single job. Put the HiPSCatalogGenerator into
a config file of its own, so that the other tasks are not re-run by every job. `--tasks.init_args.*`
on the command line sets the parameters of the last task in the list:

```bash
# Slurm array job with --array=0-19, one job per shard
hipster --config gaia_catalog.yaml --overwrite \
  --tasks.init_args.stage encode \
  --tasks.init_args.num_shards 20 \
  --tasks.init_args.shard_index $SLURM_ARRAY_TASK_ID

# afterwards, a single job
hipster --config gaia_catalog.yaml --overwrite --tasks.init_args.stage build
```

The HTML page then only contains the catalog. Regenerate it with the full config and
`--only_html --overwrite`.

A warning is printed if the HiPS catalog contains fewer objects than the input.

## Image makers

The `image_maker` of a task turns the model output into a tile image.

| Class | Purpose |
|---|---|
| {class}`~hipster.ImagePlotter` | 2D images, e.g. galaxy images. |
| {class}`~hipster.SpectrumPlotter` | Spectra plotted over a spectral color map. The wavelengths are given as a {class}`~hipster.Range`. |
| {class}`~hipster.AbsorptionLinePlotter` | Spectra plotted as absorption lines. |

## Models

Encoders and decoders are ONNX models, e.g. exported from Spherinator, loaded with
{class}`hipster.Inference`. Set `model_path`, and `input_name` if the model input is not called
`x`:

```yaml
decoder:
  model_path: decoder.onnx
  input_name: z
```

See the {doc}`API reference <api>` for all parameters.
