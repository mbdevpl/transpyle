#!/usr/bin/env bash
set -Eeuxo pipefail

# OFP XML installer
# updated: 2019-05-10

# on Linux, use OFP XML from repo
if [[ "$(uname)" == "Linux" ]]; then
  git clone "https://github.com/mbdevpl/open-fortran-parser-xml" "../open-fortran-parser-xml"
  cd "../open-fortran-parser-xml"
  pip install -U -r dev_requirements.txt
  python -m open_fortran_parser --deps
  ant
  python setup.py bdist_wheel
  pip install -U dist/*.whl
  cd -
fi
