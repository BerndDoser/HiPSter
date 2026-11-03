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
{class}`~hipster.VOTableGenerator` with the final `html.url` as well. The same applies to the
`hips_service_url` in the `properties` file of a {class}`~hipster.HiPSCatalogGenerator`, which is
set by its `build` stage.

## Hosting Aladin Lite

By default the page imports Aladin Lite from the npm package on jsDelivr. To serve it yourself,
copy `dist/aladin.js` of the [`aladin-lite`](https://www.npmjs.com/package/aladin-lite) package
to your web server and set `html.aladin_lite_url`, where `{version}` is replaced by
`html.aladin_lite_version`:

```yaml
html:
  aladin_lite_version: 3.6.5
  aladin_lite_url: https://example.org/aladin-lite/{version}/aladin.js
```

The file is an ES module, so it must be served as `text/javascript`, and with an
`Access-Control-Allow-Origin` header if pages on other origins import it.
