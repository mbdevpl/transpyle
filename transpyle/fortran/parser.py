
import pathlib
import xml.etree.ElementTree as ET

import open_fortran_parser

from ..general import Language, Parser

class FortranParser(Parser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def parse(self, input_path: pathlib.Path, verbosity: int = 100) -> ET.Element:
        return open_fortran_parser.parse(input_path, verbosity, raise_on_error=True)
