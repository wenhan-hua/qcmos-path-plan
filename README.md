# qCMOS path plan

Beam-path plan for imaging single atoms in optical tweezers (1 µm waist) onto a **Hamamatsu qCMOS (C15550-22UP)** and a **Basler acA4029-29um**, split by one dichroic mirror.
Contains 2D diagrams (Inkscape/ComponentLibrary glyphs), a to-scale interactive 3D table layout, and the scripts that generate both.

**Current revision: 2026-11-23**

## The plan

```
FoV (1×1 mm) → static objective (EFL 10 mm) → M (1″/2″) → M (2″) → L1 f=150 mm (2″) → DM  Thorlabs DMSP1000L (2″ shortpass)

 T port (852 nm):  M (2″) → M (2″) → L2 f=150 mm → M (2″) → M (1″) → 852 nm line filters (≥1, last one before L3) → L3 f=40 mm (or 50) → qCMOS
 R port (1030 nm): M (2″) → M (2″) → L4 f=100 mm → M (2″) → M (1″) → L5 f=40 mm → Basler
```

All beams are at the height of the static-objective axis (4″ / 101.6 mm in the 3D model).
Only two 150 mm achromats are available in the lab (L1, L2), so the Basler relay uses a spare **100 mm** lens (L4).

### Magnification (M = 150/10 × f_last / f_relay)

| Camera | relay | last lens | M | 1 µm waist | 1 mm FoV on sensor | fits sensor? |
|---|---|---|---|---|---|---|
| qCMOS 18.8×10.6 mm, 4.6 µm px | L2 = 150 | L3 = 40 mm | 4.0× | 4.0 µm = 0.87 px | 4.0 mm | yes |
| qCMOS | L2 = 150 | L3 = 50 mm | 5.0× | 5.0 µm = 1.09 px | 5.0 mm | yes |
| Basler 7.5×5.6 mm, 1.85 µm px | L4 = 100 | L5 = 40 mm | 6.0× (0.31 µm/px) | 6.0 µm | 6.0 mm | **no: 7 % over the 5.6 mm height** (usable FoV 1.25 × 0.93 mm) |

Full 1 mm FoV on the Basler needs f(L5) ≤ 37 mm (e.g. 35 mm → 5.25×, 0.35 µm/px).
Relay geometry: the intermediate image is 150 mm after L1, so L1 → L2 = 300 mm and L1 → L4 = 250 mm; last lens → sensor = f.

### Beam size / clear-aperture check  (`diagrams/beam_envelope_*.png`, `src/optics_trace.py`)

A to-scale top view with the beam drawn through every optic (paraxial trace, assumed objective NA 0.4, i.e. Ø8 mm collimated beam; exit pupil at the objective back end; FoV 1×1 mm; clear aperture = 90 % of the diameter, ×0.707 for 45° mirrors).
**Result for the current layout: the full 1×1 mm field does not pass.** Each field point leaves the f = 10 mm objective as a collimated bundle tilted by h/10 mm, and the bundles walk off the axis with distance (0.1 mm per mm of path per mm of field). With the objective back aperture 425 mm from L1 and the last lens 325 mm after the relay lens, the field-edge footprint exceeds the optics:

| branch | element | beam footprint r | allowed r | field that passes (of ±0.5 mm) |
|---|---|---|---|---|
| common | M2 (2″ mirror) | 19.5 mm | 16.2 mm | ±0.39 mm |
| common | L1 (2″) | 25.2 mm | 22.9 mm | ±0.44 mm |
| common | DM (2″) | 19.9 mm | 16.2 mm | ±0.39 mm |
| T → qCMOS | M6 (1″ mirror) / L3 (1″) | 20.0 / 26.5 mm | 8.1 / 11.4 mm | ±0.13 / ±0.17 mm |
| R → Basler | M10 (1″ mirror) / L5 (1″) | 20.1 / 26.8 mm | 8.1 / 11.4 mm | ±0.16 / ±0.18 mm |

Fix (`src/what_if.py`): keep the back aperture → L1 distance short (≈ 200 mm, still > 150 mm) and put the last lens close after the relay lens (≈ 170 mm for L2 → L3, ≈ 130 mm for L4 → L5). Then every element, including the 1″ mirrors, filters and last lenses, passes the full field (limiting element: DM, ±0.72 mm).
Not yet applied to the layout. The result scales with NA: `NA=0.3 ./build.sh envelope`.

### Open items
- Confirm the objective's NA and the position of its back aperture (the beam-size check assumes NA 0.4, pupil at the rear of the body).
- DMSP1000L: 1030 nm is only 30 nm above the 1000 nm cutoff; confirm its reflection at 1030 nm from the Thorlabs transmission data.
- L4 (100 mm) size is assumed 2″; confirm.
- 3D camera bodies are approximate envelopes (qCMOS ≈ 100×100×160 mm, Basler 29×29×42 mm).
- The "ports swapped" variant (qCMOS on R, Basler on T) needs a *longpass* DM, not the DMSP1000L. It is kept for layout comparison.

## Contents

| Path | What |
|---|---|
| `diagrams/beam_path_ports_default.{svg,pdf,png}` | 2D diagram, qCMOS on T port, Basler on R port (current plan) |
| `diagrams/beam_path_ports_swapped.{svg,pdf,png}` | same optics with the two camera paths swapped between DM ports |
| `diagrams/beam_envelope_{default,swapped}.{svg,pdf,png}` | **to-scale top view with beam size** and a clear-aperture check per optic |
| `3d/layout3d_interactive.html` | self-contained 3D viewer (open in a browser): orbit/zoom, **flip T/R ports**, iso/top/side, labels |
| `3d/renders/` | static PNG renders of the 3D layout |
| `src/` | generators: `make_diagram.py` (2D schematic), `make_envelope.py` + `optics_trace.py` (beam-size check), `what_if.py`, `layout.py` (to-scale positions), `template.html` + `build_3d.py` (3D viewer), `shot.py` (headless-Chrome renders), `cl_lib.py` (ComponentLibrary helper), `vendor/` (three.js) |
| `archive/2026-11-20/` | previous revision (R-port relay 150 mm, last lens 50/60 mm, DM unspecified) |
| `lib/` | local vendor datasheets (git-ignored, e.g. Hamamatsu manual) |

## Rebuild

```bash
./fetch_library.sh      # one-off: downloads ComponentLibrary into third_party/ (not redistributed here)
./build.sh              # 2D diagrams + beam-envelope check + 3D html          (./build.sh all  also re-renders the 3D PNGs)
```
Requires Python 3 (stdlib only), Inkscape (`INKSCAPE=/path/to/inkscape` if not in `/Applications`), and Google Chrome for the PNG renders.
To change the layout edit `src/layout.py` (positions, relay lengths) or the chain definitions in `src/make_diagram.py`.

## Third-party material
- Component glyphs: **ComponentLibrary** by Alexander Franzen, CC BY-NC 3.0 (<https://www.gwoptics.org/ComponentLibrary/>). Downloaded on demand, not committed; the generated diagrams embed some glyphs, so keep the attribution and non-commercial use.
- `src/vendor/`: three.js r147 and OrbitControls (MIT).
- No license has been chosen for the code in this repo.

## Changelog
- **2026-11-23 (later)**: added the to-scale beam-envelope / clear-aperture check (finds vignetting of the 1 mm field in the current layout); fixed the Basler sensor spacing in the 3D layout (sensor is now 40 mm behind L5, was 50 mm).
- **2026-11-23**: DM = DMSP1000L. R-port relay lens 150 → 100 mm, Basler last lens 50/60 → 40 mm (M = 6×). 3D layout and diagrams regenerated; project reorganised into `src/`, `diagrams/`, `3d/`.
- **2026-11-20**: first diagrams, port-swap variants, 3D layout.
