"""For running external tools in a slightly isolated/failsafe manner."""

import contextlib
import io
import logging
import os
import pathlib
import subprocess
import sys

import argunparse

_LOG = logging.getLogger(__name__)


def _postprocess_result(result: subprocess.CompletedProcess) -> None:
    if isinstance(result.stdout, bytes):
        result.stdout = result.stdout.decode('utf-8', 'ignore')
    if isinstance(result.stderr, bytes):
        result.stderr = result.stderr.decode('utf-8', 'ignore')
    if len(result.stderr) > 10240:
        result.stderr = result.stderr[:10240]


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


def _fileno(file_or_fd):
    fd_ = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd_, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd_


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
    _postprocess_result(result)
    if result.returncode != 0:
        _LOG.error('%s', result)
        raise RuntimeError('execution of "{}" failed: {}'.format(executable.name, result))
    return result


def call_tool(function, args=(), kwargs=None, cwd: pathlib.Path = None,
              commandline_equivalent: str = None) -> subprocess.CompletedProcess:
    """Call a given function with given arguments and report result as if it was a subprocess.

    Assumption is that the function returns a numeric return code, just as a subprocess would.
    """
    if kwargs is None:
        kwargs = {}
    stdout = io.StringIO()
    stderr = io.StringIO()
    _LOG.debug('calling tool %s(*%s, **%s) (simulating: %s) ...',
               function, args, kwargs, commandline_equivalent)
    with temporarily_change_dir(cwd):
        with redirect_stdout_and_stderr(stdout, stderr):
            returncode = function(*args, **kwargs)
    if commandline_equivalent is None:
        argunparser = argunparse.ArgumentUnparser()
        commandline_equivalent = '{} {}'.format(
            function.__name__, argunparser.unparse_options_and_args(kwargs, args))
    result = subprocess.CompletedProcess(
        args=commandline_equivalent, stdout=stdout.getvalue(), stderr=stderr.getvalue(),
        returncode=returncode)
    _postprocess_result(result)
    if result.returncode != 0:
        raise RuntimeError('execution of {}() failed: {}'.format(function.__name__, result))
    return result
