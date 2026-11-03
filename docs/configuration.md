# Configuration

HiPSter is run from the command line and configured with a YAML file:

```bash
hipster --config <path_to_config_file>
```

## Command line options

| Option | Description |
|---|---|
| `--config` | Path to the config file. |
| `--root_path` | Output directory for all tasks and the HTML page. Defaults to `./HiPSter`. |
| `--only_html` | Only (re)generate the HTML page, skip the tasks. |
| `--overwrite` | Allow writing into an existing `root_path`. |
| `-v`, `--verbose` | Print the base URL and the list of tasks. |
| `--version` | Print the version and exit. |

Every value of the config file can also be set or overridden on the command line, e.g.
`--html.title "My HiPS"`. Run `hipster --help` for the full list.

## Configuration file

A configuration file has three parts:

- `root_path`: the output directory, which is passed on to the HTML page and all tasks.
- `html`: settings for the generated Aladin Lite page (`url`, `title`, `aladin_lite_version`),
  see {class}`hipster.HTMLGenerator` and {doc}`visualization`.
- `tasks`: a list of {doc}`tasks <tasks>`, each given by a `class_path` and its `init_args`. They
  are executed in order and each one adds an image layer or a catalog to the HTML page. Set
  `skip: true` to keep a task on the page without re-running it.

```yaml
root_path: HiPSter
html:
  url: http://localhost:8083
  title: HiPSter representation of Gaia XP DR3
  aladin_lite_version: latest
tasks:
  - class_path: hipster.HiPSGenerator
    init_args:
      decoder:
        model_path: decoder.onnx
      image_maker:
        class_path: hipster.SpectrumPlotter
        init_args:
          wavelengths:
            start: 336
            stop: 1021
            step: 2
          ylim: [0, 1]
          margin: 0.02
          figsize_in_pixel: 128
          flip: True
      hips_id: Gaia1
      hips_name: Gaia XP DR3 model spectrum
      hips_path: gaia/model_spectrum
      max_order: 2
      hierarchy: 2
  - class_path: hipster.VOTableGenerator
    init_args:
      encoder:
        model_path: encoder.onnx
      data_directory: data/gaia/xp_calibrated
      color: red
      shape: circle
      size: 10
```

More complete configurations are in the
[`examples/`](https://github.com/HITS-AIN/HiPSter/tree/main/examples) directory.
