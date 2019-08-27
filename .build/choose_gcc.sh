#!/usr/bin/env bash
set -Eeuxo pipefail

# if [[ "$(uname)" == "Linux" ]]; then
#   sudo update-alternatives \
#     --install /usr/local/bin/gcc gcc /usr/bin/gcc-7 70 \
#     --slave /usr/local/bin/g++ g++ /usr/bin/g++-7 \
#     --slave /usr/local/bin/cpp gcc-cpp /usr/bin/cpp-7 \
#     --slave /usr/local/bin/gfortran gfortran /usr/bin/gfortran-7 \
#     --slave /usr/local/bin/gcc-ar gcc-ar /usr/bin/gcc-ar-7 \
#     --slave /usr/local/bin/gcc-nm gcc-nm /usr/bin/gcc-nm-7 \
#     --slave /usr/local/bin/gcc-ranlib gcc-ranlib /usr/bin/gcc-ranlib-7 \
#     --slave /usr/local/bin/gcov gcov /usr/bin/gcov-7 \
#     --slave /usr/local/bin/gcov-dump gcov-dump /usr/bin/gcov-dump-7
#   sudo update-alternatives --install /usr/bin/cc cc /usr/local/bin/gcc 100
#   sudo update-alternatives --install /usr/bin/c++ c++ /usr/local/bin/g++ 100
#   sudo update-alternatives --install /lib/cpp cpp /usr/local/bin/cpp 100
#   sudo update-alternatives --install /usr/bin/f77 f77 /usr/local/bin/gfortran 100
#   sudo update-alternatives --install /usr/bin/f95 f95 /usr/local/bin/gfortran 100
# fi

if [[ "$(uname)" == "Darwin" ]]; then
  set -Eeuxo pipefail
  sudo ln -s /usr/local/bin/gcc-$1 /usr/local/bin/gcc
  sudo ln -s /usr/local/bin/g++-$1 /usr/local/bin/g++
  sudo ln -s /usr/local/bin/cpp-$1 /usr/local/bin/cpp
  # sudo ln -s /usr/local/bin/gfortran-$1 /usr/local/bin/gfortran  # already exists
  sudo ln -s /usr/local/bin/gcc-ar-$1 /usr/local/bin/gcc-ar
  sudo ln -s /usr/local/bin/gcc-nm-$1 /usr/local/bin/gcc-nm
  sudo ln -s /usr/local/bin/gcc-ranlib-$1 /usr/local/bin/gcc-ranlib
  sudo ln -s /usr/local/bin/gcov-$1 /usr/local/bin/gcov
  sudo ln -s /usr/local/bin/gcov-dump-$1 /usr/local/bin/gcov-dump
fi
