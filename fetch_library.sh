#!/bin/bash
# Download Alexander Franzen's ComponentLibrary (CC BY-NC 3.0) into third_party/. Not redistributed in this repo.
set -e
cd "$(dirname "$0")"
mkdir -p third_party/ComponentLibrary && cd third_party/ComponentLibrary
curl -sL -O https://www.gwoptics.org/ComponentLibrary/ComponentLibrary_svg.zip
unzip -q -o ComponentLibrary_svg.zip
echo "ok: $(pwd)/ComponentLibrary_svg/ComponentLibrary.svg"
