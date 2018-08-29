FROM mbdevpl/usable-ubuntu:18.04

MAINTAINER Mateusz Bysiek <mateusz.bysiek.spam@gmail.com>

USER user
RUN mkdir -p "/home/user/.local/bin" && \
  mkdir -p "/home/user/Projects"

#
# clone dependencies and tested apps
#

WORKDIR /home/user/Projects
RUN \
  git clone "https://github.com/CodethinkLabs/ofc" open-fortran-compiler && \
  # git clone "https://github.com/mbdevpl/open-fortran-parser" && \
  git clone "https://github.com/mbdevpl/open-fortran-parser-xml" && \
  git clone "https://github.com/CastXML/CastXML" && \
  git clone "https://github.com/mbdevpl/ffb-mini" && \
  git clone "https://github.com/mbdevpl/miranda_io"

#
# build dependencies
#

WORKDIR /home/user/Projects/open-fortran-compiler

RUN CFLAGS="-Wno-implicit-fallthrough -Wno-maybe-uninitialized" make && \
  ln -s "$(pwd)/ofc" "/home/user/.local/bin/ofc"

WORKDIR /home/user/Projects/open-fortran-parser-xml

RUN pip3.6 install --user -r requirements.txt && \
  python3.6 -m open_fortran_parser --dev-deps && \
  ant && \
  python3.6 setup.py bdist_wheel && \
  pip3.6 install --user dist/*.whl && \
  python3.6 setup.py clean --all && \
  ant clean

WORKDIR /home/user/Projects/CastXML

RUN cmake . && \
  make && \
  ln -s "$(pwd)/bin/castxml" "/home/user/.local/bin/castxml"

#
# transpyle
#

COPY . /home/user/Projects/transpyle

WORKDIR /home/user/Projects/transpyle
RUN sudo chown -R user:user /home/user/Projects/transpyle && \
  git clean -f -d -x && \
  pip3.6 install --user -r test_requirements.txt && \
  python3.6 setup.py bdist_wheel && \
  pip3.6 install --user dist/*
