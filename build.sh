#!/bin/bash
# Rebuild everything, for every variant (or one):   ./build.sh [diagrams|envelope|html|renders|all] [variant]
#   default target: diagrams + envelope + html      variants: L4-100_L5-40 (current plan), L4-250_L5-100 (trial)
#   outputs go to variants/<variant>/{diagrams,3d}
# Needs: python3 (stdlib only), Inkscape (INKSCAPE=... if not in /Applications), Google Chrome (3D PNG renders).
#   NA=0.55 ./build.sh envelope     (objective NA assumed for the beam-size check; default 0.55)
set -e
cd "$(dirname "$0")"
INK="${INKSCAPE:-/Applications/Inkscape.app/Contents/MacOS/inkscape}"
LIB=third_party/ComponentLibrary/ComponentLibrary_svg/ComponentLibrary.svg
what="${1:-default}"
VARIANTS="${2:-L4-100_L5-40 L4-250_L5-100}"

diagrams() {
  [ -f "$LIB" ] || ./fetch_library.sh
  mkdir -p "$D"
  for v in default swapped; do
    n="$D/beam_path_ports_$v"; flip=""; [ $v = swapped ] && flip=flip
    python3 -I src/make_diagram.py "$PWD/src" "$LIB" "$INK" "$n.svg" $flip
    "$INK" --vacuum-defs --export-filename="$n.svg" "$n.svg" >/dev/null 2>&1
    "$INK" --export-type=pdf --export-text-to-path "$n.svg" --export-filename="$n.pdf" >/dev/null 2>&1
    "$INK" --export-type=png --export-width=3400 --export-background=white "$n.svg" --export-filename="$n.png" >/dev/null 2>&1
  done
}
envelope() {
  [ -f "$LIB" ] || ./fetch_library.sh
  mkdir -p "$D"
  for v in default swapped; do
    n="$D/beam_envelope_$v"
    python3 -I src/make_envelope.py "$PWD/src" "$LIB" "$INK" "$n.svg" $v ${NA:-0.55}
    "$INK" --vacuum-defs --export-filename="$n.svg" "$n.svg" >/dev/null 2>&1
    "$INK" --export-type=pdf --export-text-to-path "$n.svg" --export-filename="$n.pdf" >/dev/null 2>&1
    "$INK" --export-type=png --export-width=2400 --export-background=white "$n.svg" --export-filename="$n.png" >/dev/null 2>&1
  done
}
html() { mkdir -p "$T"; python3 -I src/build_3d.py "$PWD/$T/layout3d_interactive.html"; }
renders() {
  mkdir -p "$T/renders"
  C="Imaging+path+%E2%80%93+3D+layout"; V="${VAR/_/+%2F+}"
  Dd="qCMOS+on+T+port+%C2%B7+Basler+on+R+port+%C2%B7+$V"; S="qCMOS+on+R+port+%C2%B7+Basler+on+T+port+%C2%B7+$V"
  H="$PWD/$T/layout3d_interactive.html"
  python3 -I src/shot.py "$H" "view=iso&variant=default&cap=$C&sub=$Dd" "$T/renders/layout3d_default_iso.png" 1800 1190
  python3 -I src/shot.py "$H" "view=top&variant=default&cap=$C+%28top%29&sub=$Dd" "$T/renders/layout3d_default_top.png" 1800 1190
  python3 -I src/shot.py "$H" "view=side&variant=default&labels=0&cap=$C+%28side%29&sub=$Dd" "$T/renders/layout3d_default_side.png" 1800 1190
  python3 -I src/shot.py "$H" "view=iso&variant=swapped&cap=$C&sub=$S" "$T/renders/layout3d_swapped_iso.png" 1800 1190
  python3 -I src/shot.py "$H" "view=top&variant=swapped&cap=$C+%28top%29&sub=$S" "$T/renders/layout3d_swapped_top.png" 1800 1190
}
for VAR in $VARIANTS; do
  export QVARIANT="$VAR"; D="variants/$VAR/diagrams"; T="variants/$VAR/3d"
  echo "== variant $VAR"
  case "$what" in
    diagrams) diagrams;; envelope) envelope;; html) html;; renders) renders;;
    all) diagrams; envelope; html; renders;; *) diagrams; envelope; html;;
  esac
done
