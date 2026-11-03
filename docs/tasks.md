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
| {class}`~hipster.NumberedHiPSGenerator` | Labels each HiPS tile with its order and pixel number, useful to check the tiling. No model required. |

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
