#!/usr/bin/env bash
set -Eeuxo pipefail

# CastXML installer
# updated: 2019-08-28

git clone "https://github.com/CastXML/CastXML" "../CastXML"
cd "../CastXML"
CC=clang CXX=clang++ cmake . -DLLVM_DIR=$(llvm-config --cmakedir)
make
# export PATH="$(pwd)/bin:${PATH}"
mkdir -p "${HOME}/.local/bin"
ln -s "$(pwd)/bin/castxml" "${HOME}/.local/bin/castxml"
cd -
