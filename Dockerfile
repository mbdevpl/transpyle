FROM mbdevpl/usable-python:ubuntu16.04

MAINTAINER Mateusz Bysiek <mateusz.bysiek.spam@gmail.com>

USER user
WORKDIR /home/user

RUN mkdir -p Projects

#
# Open Fortran Compiler
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/CodethinkLabs/ofc open-fortran-compiler

WORKDIR /home/user/Projects/open-fortran-compiler

RUN CC=gcc-5 make
RUN export PATH="$(pwd):${PATH}"

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
# apps
#

WORKDIR /home/user/Projects
RUN git clone https://github.com/mbdevpl/ffb-mini

RUN git clone https://github.com/mbdevpl/miranda_io

#
# transpyle
#

COPY . /home/user/Projects/transpyle
RUN sudo chown -R user:user /home/user/Projects/transpyle

WORKDIR /home/user/Projects/transpyle
RUN git clean -f -d

RUN pip3.6 install --user -r test_requirements.txt
RUN python3.6 setup.py bdist_wheel
RUN pip3.6 install --user dist/*

#WORKDIR /home/user/Projects/transpyle

#RUN python3.6 -m unittest test.test_apps.Tests.test_roundtrip_flash


#WORKDIR /home/user/Projects/python

#WORKDIR /home/user
