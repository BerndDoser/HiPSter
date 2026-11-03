# Visualization

HiPSter writes an `index.html` into `root_path` that shows all HiPS layers and catalogs in
[Aladin Lite](https://github.com/cds-astro/aladin-lite).

## Local server

The page loads the layers from `html.url`, so `root_path` must be served at that URL. With the
default `http://localhost:8083`, any static web server works:

```bash
cd <root_path>
python3 -m http.server 8083
```

and open <http://localhost:8083> in a browser. In a clone of the repository, `src/server.py`
starts the same server on port 8083 with CORS headers enabled.

## Publishing on a web server

To publish the result elsewhere, regenerate the page for the new URL without re-running the tasks:

```bash
hipster --config <path_to_config_file> --only_html --overwrite --html.url https://example.org/hipster
```

Then copy `root_path` to the web server so that it is served at that URL. The preview links inside a VOTable catalog are written when the catalog is generated, so re-run the
{class}`~hipster.VOTableGenerator` with the final `html.url` as well.
