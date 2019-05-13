#!/usr/bin/env bash
set -Eeuxo pipefail

# CastXML installer
# updated: 2019-05-10

git clone "https://github.com/CastXML/CastXML" "../CastXML"
cd "../CastXML"
if [[ "${TRAVIS_OS_NAME}" == "osx" ]]; then
  CC=clang CXX=clang++ cmake .
else
  cmake .
fi
make
# export PATH="$(pwd)/bin:${PATH}"
ln -s "$(pwd)/bin/castxml" "${HOME}/.local/bin/castxml"
cd -
