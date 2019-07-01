"""Fortran Parser which simply delegates the work to Open Fortran Parser XML generator."""

import pathlib
import xml.etree.ElementTree as ET

import open_fortran_parser

from ..general import Parser
from ..general.tools import summarize_completed_process


class FortranParser(Parser):

    def _parse_scope(self, code: str, path: pathlib.Path = None) -> ET.Element:
        assert path is not None, path
        result = open_fortran_parser.execute_parser(path, None, verbosity=100)
        try:
            stdout_str = result.stdout.decode()
            xml = ET.fromstring(stdout_str)
        except ET.ParseError:
            result.returncode = -1
        summarize_completed_process(result, executable=pathlib.Path('open_fortran_parser'))
        return xml
