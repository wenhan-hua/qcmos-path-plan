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

### Real spacings in the layout (beam path, mm; `src/layout.py`, verified by `src/check_layout.py`)

| segment | mm | rule |
|---|---|---|
| objective back aperture → L1 (via M1, M2) | **170** | must be ≥ 150 |
| L1 → L2 (qCMOS branch, via DM, 2 mirrors) | 300 | f(L1) + f(L2) = 150 + 150 |
| L1 → L4 (Basler branch, via DM, 2 mirrors) | 250 | 150 + 100 |
| L2 → L3 (M5, M6, 2 filters) | 180 | kept short, see below |
| L4 → L5 (M9, M10) | 155 | kept short |
| L3 → qCMOS sensor / L5 → Basler sensor | 40 / 40 | = f of the last lens |

`check_layout.py` also confirms that the sensors sit at the image plane (M = 4.0× and 6.0×) and that no two mounts, nor a beam and a foreign mount, come within 3 mm in plan view (both port assignments).

### Beam size / clear-aperture check  (`diagrams/beam_envelope_*.png`, `src/optics_trace.py`)

A to-scale top view with the beam drawn through every optic (paraxial trace). Inputs: objective **NA 0.55** (EFL 10 mm → Ø11 mm collimated beam), exit pupil at the rear of the objective, FoV 1×1 mm, thin lenses, clear aperture = 90 % of the diameter (×0.707 for 45° mirrors), L4 = 2″.
Each field point leaves the f = 10 mm objective as a collimated bundle tilted by h/10, and the bundles walk off the axis with distance, so the 1″ optics only pass the whole field if the legs after the objective and the relay lens are short.

**Current layout: the full 1×1 mm field passes every optic** (tightest element: the DM, ±0.75 mm of field vs 0.71 mm needed for the corners; the 1″ M6 / M10 and last lenses have > 25 % margin).
For comparison, the first layout (back aperture → L1 = 425 mm, L2 → L3 = 325 mm) passed only about ±0.1 mm of the ±0.5 mm field through the 1″ mirrors, filters and last lenses.
`src/what_if.py` reproduces both. The result scales with NA: `NA=0.4 ./build.sh envelope`.

### Open items
- The beam-size check puts the objective's exit pupil at the rear of the body (70 mm from the FoV); confirm the real pupil position from the objective's drawing.
- DMSP1000L: 1030 nm is only 30 nm above the 1000 nm cutoff; confirm its reflection at 1030 nm from the Thorlabs transmission data.
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
| `src/` | generators: `make_diagram.py` (2D schematic), `make_envelope.py` + `optics_trace.py` (beam-size check), `check_layout.py` (spacings + collisions), `what_if.py`, `layout.py` (to-scale positions), `template.html` + `build_3d.py` (3D viewer), `shot.py` (headless-Chrome renders), `cl_lib.py` (ComponentLibrary helper), `vendor/` (three.js) |
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
- **2026-11-23 (compact layout)**: objective NA 0.55 and L4 = 2″ confirmed. Front end compacted (back aperture → L1 = 170 mm) and post-relay legs shortened so the full 1 mm field clears every optic; diagrams, envelope figures and 3D model regenerated; added `check_layout.py`.
- **2026-11-23 (earlier)**: added the to-scale beam-envelope / clear-aperture check (found vignetting in the first layout); fixed the Basler sensor spacing in the 3D layout (sensor 40 mm behind L5, was 50 mm).
- **2026-11-23**: DM = DMSP1000L. R-port relay lens 150 → 100 mm, Basler last lens 50/60 → 40 mm (M = 6×). 3D layout and diagrams regenerated; project reorganised into `src/`, `diagrams/`, `3d/`.
- **2026-11-20**: first diagrams, port-swap variants, 3D layout.
