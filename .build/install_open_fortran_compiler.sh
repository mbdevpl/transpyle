#!/usr/bin/env bash
set -Eeuxo pipefail

# Open Fortran Compiler installer
# updated: 2019-05-10

git clone "https://github.com/codethinklabs/ofc" "../open-fortran-compiler"
cd "../open-fortran-compiler"
if [[ "$(uname)" == "Linux" ]]; then
  CFLAGS="-Wno-implicit-fallthrough -Wno-maybe-uninitialized" make
else
  # CC=gcc  # this should work, but doesn't
  CFLAGS="-Wno-implicit-fallthrough -Wno-maybe-uninitialized" make
fi
# export PATH="$(pwd):${PATH}"
mkdir -p "${HOME}/.local/bin"
ln -s "$(pwd)/ofc" "${HOME}/.local/bin/ofc"
cd -
