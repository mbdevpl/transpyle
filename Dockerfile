FROM mbdevpl/usable-python:ubuntu16.04

MAINTAINER Mateusz Bysiek <mateusz.bysiek.spam@gmail.com>

USER user
WORKDIR /home/user

RUN mkdir -p "/home/user/.local/bin"

RUN mkdir -p Projects

#
# Open Fortran Compiler
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/CodethinkLabs/ofc open-fortran-compiler

WORKDIR /home/user/Projects/open-fortran-compiler

RUN CC=gcc-5 make
RUN ln -s "$(pwd)/ofc" "/home/user/.local/bin/ofc"

#
# Open Fortran Paresr
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/mbdevpl/open-fortran-parser

#
# Open Fortran Paresr XML
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/mbdevpl/open-fortran-parser-xml

WORKDIR /home/user/Projects/open-fortran-parser-xml

RUN pip3.6 install --user -r requirements.txt
RUN python3.6 -m open_fortran_parser --dev-deps
RUN ant
RUN python3.6 setup.py bdist_wheel
RUN pip3.6 install --user dist/*.whl

#
# CastXML
#

WORKDIR /home/user/Projects
RUN git clone "https://github.com/CastXML/CastXML"

WORKDIR /home/user/Projects/CastXML

RUN cmake .
RUN make
RUN ln -s "$(pwd)/bin/castxml" "/home/user/.local/bin/castxml"

#
# apps
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/mbdevpl/ffb-mini

RUN git clone https://github.com/mbdevpl/miranda_io

#
# transpyle
#

COPY . /home/user/Projects/transpyle
USER root
RUN chown -R user:user /home/user/Projects/transpyle
USER user

WORKDIR /home/user/Projects/transpyle
RUN git clean -f -d -x

RUN pip3.6 install --user -r test_requirements.txt
RUN python3.6 setup.py bdist_wheel
RUN pip3.6 install --user dist/*
