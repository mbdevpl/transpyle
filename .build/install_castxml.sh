#!/usr/bin/env bash
set -Eeuxo pipefail

# CastXML installer
# updated: 2019-05-10

git clone "https://github.com/CastXML/CastXML" "../CastXML"
cd "../CastXML"
if [[ "$(uname)" == "Linux" ]]; then
  cmake . -DLLVM_DIR=$(llvm-config --prefix)
else
  CC=clang CXX=clang++ cmake . -DLLVM_DIR=$(llvm-config --prefix)
fi
make
# export PATH="$(pwd)/bin:${PATH}"
mkdir -p "${HOME}/.local/bin"
ln -s "$(pwd)/bin/castxml" "${HOME}/.local/bin/castxml"
cd -
