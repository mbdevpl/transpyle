
import argparse

import static_typing as st

from .general.code_reader import CodeReader
#from .lang.cpp14.unparser import Cpp11Unparser


def main(args=None, namespace=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('target')

    args = parser.parse_args(args, namespace)

    file_path = 'test/examples/python3/gemm.py'
    ext = '.py'

    reader = CodeReader(ext)
    #path = pathlib.Path()
    code = reader.read_file(file_path)
    st.parse(code)

    Cpp11Unparser()
