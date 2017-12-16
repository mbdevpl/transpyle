"""Fortran Parser which simply delegates the work to Open Fortran Parser XML generator."""

import pathlib
import xml.etree.ElementTree as ET

import open_fortran_parser

from ..general import Language, Parser


class FortranParser(Parser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def parse(self, code: str, path: pathlib.Path = None) -> ET.Element:
        assert path is not None, path
        return open_fortran_parser.parse(path, verbosity=100, raise_on_error=True)
