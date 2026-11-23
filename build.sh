#!/bin/bash
# Rebuild everything.   ./build.sh [diagrams|envelope|html|renders|all]     (default: diagrams + envelope + html)
# envelope: NA=0.4 ./build.sh envelope   (objective NA assumed for the beam-size check)
# Needs: python3 (stdlib only), Inkscape (set INKSCAPE=... if not in /Applications), Google Chrome (for 3D PNG renders).
set -e
cd "$(dirname "$0")"
INK="${INKSCAPE:-/Applications/Inkscape.app/Contents/MacOS/inkscape}"
LIB=third_party/ComponentLibrary/ComponentLibrary_svg/ComponentLibrary.svg
what="${1:-default}"

diagrams() {
  [ -f "$LIB" ] || ./fetch_library.sh
  mkdir -p diagrams
  for v in default swapped; do
    n=diagrams/beam_path_ports_$v; flip=""; [ $v = swapped ] && flip=flip
    python3 -I src/make_diagram.py "$PWD/src" "$LIB" "$INK" $n.svg $flip
    "$INK" --vacuum-defs --export-filename=$n.svg $n.svg >/dev/null 2>&1
    "$INK" --export-type=pdf --export-text-to-path $n.svg --export-filename=$n.pdf >/dev/null 2>&1
    "$INK" --export-type=png --export-width=3400 --export-background=white $n.svg --export-filename=$n.png >/dev/null 2>&1
  done
}
envelope() {
  [ -f "$LIB" ] || ./fetch_library.sh
  for v in default swapped; do
    n=diagrams/beam_envelope_$v
    python3 -I src/make_envelope.py "$PWD/src" "$LIB" "$INK" $n.svg $v ${NA:-0.4}
    "$INK" --vacuum-defs --export-filename=$n.svg $n.svg >/dev/null 2>&1
    "$INK" --export-type=pdf --export-text-to-path $n.svg --export-filename=$n.pdf >/dev/null 2>&1
    "$INK" --export-type=png --export-width=2400 --export-background=white $n.svg --export-filename=$n.png >/dev/null 2>&1
  done
}
html() { mkdir -p 3d; python3 -I src/build_3d.py "$PWD/3d/layout3d_interactive.html"; }
renders() {
  mkdir -p 3d/renders
  C="Imaging+path+%E2%80%93+3D+layout"
  D="qCMOS+on+T+port+%C2%B7+Basler+on+R+port+(DMSP1000L+shortpass)"; S="qCMOS+on+R+port+%C2%B7+Basler+on+T+port+(longpass+DM)"
  H="$PWD/3d/layout3d_interactive.html"
  python3 -I src/shot.py "$H" "view=iso&variant=default&cap=$C&sub=$D" 3d/renders/layout3d_default_iso.png 1800 1190
  python3 -I src/shot.py "$H" "view=top&variant=default&cap=$C+%28top%29&sub=$D" 3d/renders/layout3d_default_top.png 1800 1190
  python3 -I src/shot.py "$H" "view=side&variant=default&labels=0&cap=$C+%28side%29&sub=$D" 3d/renders/layout3d_default_side.png 1800 1190
  python3 -I src/shot.py "$H" "view=iso&variant=swapped&cap=$C&sub=$S" 3d/renders/layout3d_swapped_iso.png 1800 1190
  python3 -I src/shot.py "$H" "view=top&variant=swapped&cap=$C+%28top%29&sub=$S" 3d/renders/layout3d_swapped_top.png 1800 1190
}
case "$what" in
  diagrams) diagrams;; envelope) envelope;; html) html;; renders) renders;; all) diagrams; envelope; html; renders;; *) diagrams; envelope; html;;
esac
