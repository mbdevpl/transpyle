
import pathlib
import xml.etree.ElementTree as ET

import open_fortran_parser

from ..general import Language, Parser

class FortranParser(Parser):

    def __init__(self):
        super().__init__(Language.find('Fortran 2008'))

    def parse(self, input_path: pathlib.Path, verbosity: int = 100) -> ET.Element:
        #_ = open_fortran_parser.execute_parser(input_path, pathlib.Path('/tmp', 'transpyle_' + input_path.name + '.xml'), verbosity)
        return open_fortran_parser.parse(input_path, verbosity, raise_on_error=True)
