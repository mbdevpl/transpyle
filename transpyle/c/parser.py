"""Parsing of C language."""

import io
import logging
import pathlib
import tempfile
import typing as t

import pcpp
from pcpp.preprocessor import LexToken  # ply.lex.LexToken

# import pcpp.ply as ply
import pycparser

from ..general import CodeReader, CodeWriter, Parser
from ..general.tools import run_tool

_LOG = logging.getLogger(__name__)

_HERE = pathlib.Path(__file__).resolve().parent

TRANSPYLE_C_RESOURCES_PATH = _HERE.joinpath('..', 'resources', 'c').resolve()

C_SUPPORTED_HEADERS = {'stdbool.h', 'stdio.h', 'stdlib.h', 'string.h'}

# PYCPARSER_INCLUDES = list(pathlib.Path(_, 'utils', 'fake_libc_include').glob('ls')
#                           for _ in pycparser.__path__)


class C99Preprocessor(pcpp.Preprocessor):

    """Override these in your subclass of Preprocessor to customise preprocessing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_names = []
        self.i = 0

    def include(self, tokens: t.List[LexToken]) -> t.List[LexToken]:
        if not tokens:
            return []
        _LOG.debug('%i tokens: %s', len(tokens), tokens)
        include_name = None
        if len(tokens) >= 2 and tokens[0].value == '<' and tokens[-1].value == '>':
            include_name = ''.join([_.value for _ in tokens[1:-1]])
            self.include_names.append(include_name)
        if include_name is not None and include_name in C_SUPPORTED_HEADERS:
            _LOG.info('refactoring #include%s', ''.join([_.value for _ in tokens]))
        else:
            _LOG.warning('unsupported #include%s', ''.join([_.value for _ in tokens]))
        # return []
        # yield from super().include(tokens)
        # tokens[0].value = '/* #include' + tokens[0].value
        self.i += 1
        tokens[0].value = 'const char* directive_{} = "#include{}'.format(self.i, tokens[0].value)
        # for token in tokens:
        #    token.value = ' '  # ' ' * len(token.value)
        # tokens[-1].value += ' */\n'
        tokens[-1].value += '";\n'
        return tokens

    def on_error(self, file, line, msg):
        """Called when the preprocessor has encountered an error, e.g. malformed input.

        The default simply prints to stderr and increments the return code.
        """
        _LOG.error('%s:%d error: %s', file, line, msg)
        self.return_code += 1

    def on_include_not_found(self, is_system_include, curdir, includepath):
        """Called when a #include wasn't found.

        Return None to ignore, raise OutputDirective to pass through, else return
        a suitable path. Remember that Preprocessor.add_path() lets you add search paths.

        The default calls self.on_error() with a suitable error message about the
        include file not found and raises OutputDirective (pass through).
        """
        self.on_error(self.lastdirective.source, self.lastdirective.lineno,
                      'Include file "{}" not found'.format(includepath))
        raise pcpp.preprocessor.OutputDirective()

    def on_unknown_macro_in_defined_expr(self, tok):
        """Called when an expression passed to an #if contained a defined operator
        performed on something unknown.

        Return True if to treat it as defined, False if to treat it as undefined,
        raise OutputDirective to pass through without execution, or return None to
        pass through the mostly expanded #if expression apart from the unknown defined.

        The default returns False, as per the C standard.
        """
        return False

    def on_unknown_macro_in_expr(self, tok):
        """Called when an expression passed to an #if contained something unknown.

        Return what value it should be, raise OutputDirective to pass through
        without execution, or return None to pass through the mostly expanded #if
        expression apart from the unknown item.

        The default returns a token for an integer 0L, as per the C standard.
        """
        tok.type = self.t_INTEGER
        tok.value = self.t_INTEGER_TYPE("0L")
        return tok

    def on_directive_handle(self, directive, toks, ifpassthru):
        """Called when there is one of

        define, include, undef, ifdef, ifndef, if, elif, else, endif

        Return True to execute and remove from the output, return False to
        remove from the output, raise OutputDirective to pass through without
        execution, or return None to execute AND pass through to the output
        (this only works for #define, #undef).

        The default returns True (execute and remove from the output).
        """
        # print(directive)
        # if directive.value not in ('include',):
        #    raise pcpp.preprocessor.OutputDirective()
        self.lastdirective = directive
        return True

    def on_directive_unknown(self, directive, toks, ifpassthru):
        """Called when the preprocessor encounters a #directive it doesn't understand.
        This is actually quite an extensive list as it currently only understands:

        define, include, undef, ifdef, ifndef, if, elif, else, endif

        Return True or False to remove from the output, or else raise OutputDirective
        or return None to pass through into the output.

        The default handles #error and #warning by printing to stderr and returning True
        (remove from output). For everything else it returns None (pass through into output).
        """
        if directive.value == 'error':
            self.on_error(directive.source, directive.lineno, ''.join(tok.value for tok in toks))
            return True
        if directive.value == 'warning':
            _LOG.warning('%s:%d warning: %s',
                         directive.source, directive.lineno, ''.join(tok.value for tok in toks))
            return True
        return None

    def on_potential_include_guard(self, macro):
        """Called when the preprocessor encounters an #ifndef macro or an #if !defined(macro)
        as the first non-whitespace thing in a file. Unlike the other hooks, macro is a string,
        not a token.
        """
        pass

    def on_comment(self, tok):
        """Called when the preprocessor encounters a comment token. You can modify the token
        in place, or do nothing to let the comment pass through.

        The default modifies the token to become whitespace, becoming a single space if the
        comment is a block comment, else a single new line if the comment is a line comment.
        """
        if tok.type == self.t_COMMENT1:
            tok.value = ' '
        elif tok.type == self.t_COMMENT2:
            tok.value = '\n'
        tok.type = 'CPP_WS'


class C99Parser(Parser):

    """Parser for C99 based on pycparser package."""

    def __init__(self, default_scopes=None):
        super().__init__(default_scopes)
        self._preprocessor = C99Preprocessor()
        self._parser = pycparser.CParser()

    def _parse_scope(self, code: str, path: pathlib.Path = None):
        assert path is not None, 'path is required'
        path_str = str(path)
        # return pycparser.parser_file(path_str, use_cpp=False, cpp_path='cpp', cpp_args='')

        # preprocess
        # code = pycparser.preprocess_file(path_str, cpp_path='cpp', cpp_args='')
        self._preprocessor.parse(code, path_str)
        code_io = io.StringIO()
        self._preprocessor.write(code_io)
        preprocessed_code = code_io.getvalue()
        if preprocessed_code != code:
            _LOG.debug('code was preprocessed:\n%s', preprocessed_code)

        # add selected includes
        includes = ''
        for name in self._preprocessor.include_names:
            if name in C_SUPPORTED_HEADERS:
                includes = '#include<{}>\n{}'.format(name, includes)
        self._preprocessor.include_names.clear()

        if includes:
            preprocessed_code = '{}\n{}'.format(includes, preprocessed_code)
            with tempfile.TemporaryDirectory() as tmpdir:
                output_folder = pathlib.Path(tmpdir)
            output_folder.mkdir()
            _LOG.warning('running C preprocessor on file in "%s"', output_folder)
            intermediate_path = output_folder.joinpath(path.name)
            CodeWriter(path.suffix).write_file(preprocessed_code, intermediate_path)
            output_path = output_folder.joinpath(
                '{}{}{}'.format(path.stem, '_preprocessed', path.suffix))
            run_tool(pathlib.Path('gcc'), [
                '-I', str(TRANSPYLE_C_RESOURCES_PATH), '-o', output_path, '-E', intermediate_path],
                     cwd=output_folder)
            preprocessed_code = CodeReader().read_file(output_path)
            path_str = str(output_path)

        # parse
        tree = self._parser.parse(preprocessed_code, path_str)

        return tree
