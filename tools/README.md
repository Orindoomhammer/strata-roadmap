# The Strata website

`docs/` is the published site; this folder builds it. Three pages, no build
dependencies, no JavaScript framework — plain HTML, one stylesheet, and ~30
lines of vanilla JS for the node filter.

| Page | What it is |
| --- | --- |
| `docs/index.html` | Landing page: hero, features, export table, limitations, requirements |
| `docs/nodes.html` | Node reference — all 39 nodes, their pins and every parameter |
| `docs/changelog.html` | Release history, rendered from the app's `CHANGELOG.md` |

## The pages are generated, not hand-written

Most of the site is built from the `strata-rs` source, so it cannot drift from
the shipped build:

| Site content | Source of truth |
| --- | --- |
| Node list, categories, pins | `src/node_types.rs` — `NODE_TYPES`, `EXTRA_NODE_TYPES`, `OVERRIDES` |
| Every parameter, default and range | the same `FieldDef` entries |
| Node descriptions and tips | `src/tutorial.rs` — `LESSONS`, the in-app Help text |
| Blend modes, layer count | `BLEND_MODES`, `MAX_LAYERS`, `DEFAULT_LAYERS` |
| Engine export table | `src/presets.rs` — `PRESETS` |
| Tile layouts | `src/export.rs` — `LAYOUTS` (the non-demo arm) |
| Version number | `Cargo.toml` |
| Changelog | `CHANGELOG.md` (maintenance comments stripped) |

Landing-page prose is hand-written in `tools/gen.py`, adapted from
`itch/page-copy.md` and `steam/store-copy-en.txt`.

## Rebuilding

Needs Python 3.8+ and nothing else. With `strata-rs` checked out beside this
repository it finds the source by itself:

```
python tools/build.py
```

Otherwise point it at the checkout:

```
python tools/build.py C:\path\to\strata-rs
```

Preview the result:

```
python -m http.server 8099 --bind 127.0.0.1 --directory docs
```

**Rebuild after every release**, so the node reference, version number and
changelog match what shipped. Commit the regenerated `docs/` — Pages serves the
committed files, it does not run this script.

## Two nodes are documented here, not in the app

`Road` and `WaterOutput` have no entry in `tutorial.rs::LESSONS`, so the build
would leave them blank. `tools/gen.py` carries written entries for them in
`SUPPLEMENT`. **Delete the matching entry once a real lesson ships** — the
app's own text always wins.

## Images

`docs/img/` holds curated store screenshots copied from `strata-rs/steam/shots`
plus the key art from `itch/assets`. Regenerate the sources with:

```
cargo run --release --bin storeshots   # writes the .strata demo projects
steam/shots/take.sh                    # captures the PNGs
```

`walk-river.png` is 2.1 MB. Worth running the folder through an optimiser
before pointing a real domain at it.

## Publishing

The site is served from `docs/` on `main`:

1. **Settings → Pages → Build and deployment**, source **Deploy from a branch**,
   branch `main`, folder `/docs`.
2. It appears at `https://orindoomhammer.github.io/strata-roadmap/` within a
   minute or two.

`docs/.nojekyll` stops Pages running the files through Jekyll, which it would
otherwise do by default.

### A custom domain, later

1. Add the domain under **Settings → Pages → Custom domain**. GitHub commits a
   `docs/CNAME` file holding it — leave that file alone afterwards.
2. At the registrar, for an apex domain (`strata.example`) create four `A`
   records pointing at `185.199.108.153`, `185.199.109.153`, `185.199.110.153`
   and `185.199.111.153`; for a subdomain (`www.strata.example`) create one
   `CNAME` record pointing at `orindoomhammer.github.io`.
3. Wait for the DNS check to pass, then tick **Enforce HTTPS**.

Nothing in the HTML uses absolute URLs, so the same files work under the
`github.io` path and under a custom domain with no rebuild.
