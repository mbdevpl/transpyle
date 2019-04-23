"""For running external tools in a slightly isolated/failsafe manner."""

import contextlib
import io
import logging
import os
import pathlib
import platform
import subprocess
import sys
import tempfile
import typing as t

import argunparse
from colorama import Fore, Style

_LOG = logging.getLogger(__name__)


def _postprocess_result(result: subprocess.CompletedProcess) -> None:
    if isinstance(result.stdout, bytes):
        result.stdout = result.stdout.decode('utf-8', 'ignore')
    if isinstance(result.stderr, bytes):
        result.stderr = result.stderr.decode('utf-8', 'ignore')
    if len(result.stderr) > 10240:
        result.stderr = result.stderr[:10240]


def make_completed_process_report(
        result: subprocess.CompletedProcess, actual_call: t.Optional[str] = None,
        short: bool = False) -> str:
    """Create a human-readable summary of executed process."""
    out = io.StringIO()
    args_str = result.args if isinstance(result.args, str) else ' '.join(result.args)
    if actual_call is None:
        out.write('execution of "{}"'.format(args_str))
    else:
        out.write('call to {} (simulating: "{}")'.format(actual_call, args_str))
    out.write(' {}{}{}'.format(Style.BRIGHT, 'succeeded' if result.returncode == 0 else 'failed',
                               Style.NORMAL))
    if result.returncode != 0:
        out.write(' (returncode={}{}{})'.format(Fore.LIGHTRED_EX, result.returncode,
                                                Style.RESET_ALL))
    if short:
        return out.getvalue()
    out.write('\n')
    if result.stdout:
        out.write('{}stdout{}:\n'.format(Fore.CYAN, Fore.RESET))
        out.write(result.stdout.rstrip())
        out.write('\n')
    else:
        out.write('{}no stdout{}, '.format(Fore.CYAN, Fore.RESET))
    if result.stderr:
        out.write('{}stderr{}:\n'.format(Fore.CYAN, Fore.RESET))
        out.write(result.stderr.rstrip())
    else:
        out.write('{}no stderr{}, '.format(Fore.CYAN, Fore.RESET))
    # out.write('\n{}'.format(result))
    return out.getvalue()


def summarize_completed_process(result, *, executable=None, actual_call=None) -> None:
    if actual_call is not None:
        function, args, kwargs = actual_call
        _postprocess_result(result)
        if result.returncode != 0:
            _LOG.error('execution of %s() failed', function.__name__)
            _LOG.info('details of failed execution of %s(): %s', function.__name__, result)
            raise RuntimeError(make_completed_process_report(
                result, '{}(*{}, **{})'.format(function.__name__, args, kwargs)))
        return
    assert executable is not None
    _postprocess_result(result)
    if result.returncode != 0:
        _LOG.error('execution of "%s" failed', executable.name)
        _LOG.info('details of failed execution of "%s": %s', executable.name, result)
        raise RuntimeError(make_completed_process_report(result))


@contextlib.contextmanager
def fake_context_manager(*args, **kwargs):
    yield


@contextlib.contextmanager
def temporarily_change_dir(path: pathlib.Path):
    """If given path is None, it does nothing."""
    if path is None:
        yield
        return
    assert path.is_dir(), path
    _working_dir = pathlib.Path.cwd()
    try:
        os.chdir(str(path))
        yield
    finally:
        os.chdir(str(_working_dir))


@contextlib.contextmanager
def redirect_stdout_and_stderr(stdout, stderr):
    with contextlib.redirect_stdout(stdout):
        with contextlib.redirect_stderr(stderr):
            yield


def redirect_stdout_via_fd(stdout=os.devnull):
    """ Redirects stdout to another at file descriptor level. """
    return redirect_stream_via_fd(sys.stdout, stdout)


def redirect_stderr_via_fd(stderr=os.devnull):
    """ Redirects stderr to another at file descriptor level. """
    return redirect_stream_via_fd(sys.stderr, stderr)


def _fileno(file_or_fd):
    fd_ = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd_, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd_


@contextlib.contextmanager
def redirect_stream_via_fd(stream, to=os.devnull):
    """ Redirects given stream to another at file descriptor level. """

    assert stream is not None

    stream_fd = _fileno(stream)
    # copy stream_fd before it is overwritten
    # NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stream_fd), 'wb') as copied:
        stream.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(_fileno(to), stream_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stream_fd)  # $ exec > to
        try:
            yield stream  # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            # NOTE: dup2 makes stdout_fd inheritable unconditionally
            stream.flush()
            os.dup2(copied.fileno(), stream_fd)  # $ exec >&copied


@contextlib.contextmanager
def redirect_stdout_and_stderr_via_fd(stdout, stderr):
    with redirect_stdout_via_fd(stdout):
        with redirect_stderr_via_fd(stderr):
            yield


def run_tool(executable: pathlib.Path, args=(), kwargs=None, cwd: pathlib.Path = None,
             argunparser: argunparse.ArgumentUnparser = None) -> subprocess.CompletedProcess:
    """Run a given executable with given arguments."""
    if kwargs is None:
        kwargs = {}
    if argunparser is None:
        argunparser = argunparse.ArgumentUnparser()
    command = [str(executable)] + argunparser.unparse_options_and_args(kwargs, args, to_list=True)
    run_kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
    if cwd is not None:
        run_kwargs['cwd'] = str(cwd)
    _LOG.debug('running tool %s ...', command)
    result = subprocess.run(command, **run_kwargs)
    _LOG.debug('return code of "%s" tool: %s', executable, result)
    summarize_completed_process(result, executable=executable)
    return result


def call_tool(function, args=(), kwargs=None, cwd: pathlib.Path = None,
              commandline_equivalent: str = None, capture_output: bool = True
              ) -> subprocess.CompletedProcess:
    """Call a given function with given arguments and report result as if it was a subprocess.

    Assumption is that the function returns a numeric return code, just as a subprocess would.
    """
    if kwargs is None:
        kwargs = {}
    if not capture_output:
        redirector = fake_context_manager
        stdout = None
        stderr = None
    elif platform.system() == 'Linux':
        redirector = redirect_stdout_and_stderr_via_fd
        stdout = tempfile.NamedTemporaryFile('w+', delete=False)
        stderr = tempfile.NamedTemporaryFile('w+', delete=False)
    else:
        redirector = redirect_stdout_and_stderr
        stdout = io.StringIO()
        stderr = io.StringIO()
    _LOG.debug('calling tool %s(*%s, **%s) (simulating: %s) ...',
               function, args, kwargs, commandline_equivalent)
    with temporarily_change_dir(cwd):
        with redirector(stdout, stderr):
            returncode = function(*args, **kwargs)
    if not capture_output:
        stdout_str = ''
        stderr_str = ''
    elif platform.system() == 'Linux':
        with open(stdout.name) as _:
            stdout_str = _.read()
        with open(stderr.name) as _:
            stderr_str = _.read()
    else:
        stdout_str = stdout.getvalue()
        stderr_str = stderr.getvalue()
    if commandline_equivalent is None:
        argunparser = argunparse.ArgumentUnparser()
        commandline_equivalent = '{} {}'.format(
            function.__name__, argunparser.unparse_options_and_args(kwargs, args))
    result = subprocess.CompletedProcess(
        args=commandline_equivalent, stdout=stdout_str, stderr=stderr_str,
        returncode=returncode)
    summarize_completed_process(result, actual_call=(function, args, kwargs))
    return result
