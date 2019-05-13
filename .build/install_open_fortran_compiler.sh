#!/usr/bin/env bash
set -Eeuxo pipefail

# Open Fortran Compiler installer
# updated: 2019-05-10

git clone "https://github.com/codethinklabs/ofc" "../open-fortran-compiler"
cd "../open-fortran-compiler"
if [[ "${TRAVIS_OS_NAME}" == "osx" ]]; then
  # CC=gcc  # this should work
  CFLAGS="-Wno-implicit-fallthrough -Wno-maybe-uninitialized" make
else
  CFLAGS="-Wno-implicit-fallthrough -Wno-maybe-uninitialized" make
fi
# export PATH="$(pwd):${PATH}"
ln -s "$(pwd)/ofc" "${HOME}/.local/bin/ofc"
cd -
