
import itertools
import logging
import os
# import pathlib
import platform
import unittest

# from encrypted_config.path_tools import normalize_path
from encrypted_config.json_io import json_to_file
import matplotlib
import numba
import numpy as np
import timing

from transpyle.general import Language, CodeWriter, Binder, AutoTranspiler
from transpyle.cpp import CppSwigCompiler
from transpyle.fortran import F2PyCompiler
from transpyle.fortran.compiler_interface import GfortranInterface, PgifortranInterface

from .common import EXAMPLES_ROOTS, PERFORMANCE_RESULTS_ROOT, make_f2py_tmp_folder

_LOG = logging.getLogger(__name__)
_TIME = timing.get_timing_group(__name__)


class Tests(unittest.TestCase):

    def test_do_nothing(self):
        name = 'do_nothing'
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))}
        variants['py_numba'] = variants['py']
        if platform.system() == 'Linux':
            variants['cpp'] = CppSwigCompiler().compile_file(
                EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))

        transforms = {'py_numba': numba.jit}

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                with self.subTest(variant=variant, path=path):
                    # with _TIME.measure('{}.{}'.format(name, variant)) as timer:
                    for _ in _TIME.measure_many('{}.{}'.format(name, variant), 1000):
                        tested_function()
                    # _LOG.warning('timing: %s', timer)

        timings_name = '.'.join([__name__, name])
        summary = timing.query_cache(timings_name).summary
        _LOG.info('%s', summary)
        json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        if summary['py']['median'] < summary['f95']['median']:
            self.assertAlmostEqual(summary['py']['median'], summary['f95']['median'],
                                   places=5 if os.environ.get('CI') else 6)
        if platform.system() == 'Linux':
            if summary['py']['median'] < summary['cpp']['median']:
                self.assertAlmostEqual(summary['py']['median'], summary['cpp']['median'],
                                       places=5 if os.environ.get('CI') else 6)

    # @unittest.skipUnless(platform.system() == 'Linux', 'tested only on Linux')
    def test_compute_pi(self):
        name = 'compute_pi'

        # t.Dict[str, pathlib.Path]
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))
        }
        variants['py_numba'] = variants['py']
        variants['py_to_f95'] = AutoTranspiler(
            Language.find('Python'), Language.find('Fortran 95')).transpile_file(variants['py'])
        if platform.system() == 'Linux':
            variants['cpp'] = CppSwigCompiler().compile_file(
                EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))
            variants['py_to_cpp'] = AutoTranspiler(
                Language.find('Python'), Language.find('C++14')).transpile_file(variants['py'])

        # t.Dict[str, collections.abc.Callable]
        transforms = {'py_numba': numba.jit}

        segments_list = [_ for _ in range(0, 20)]

        # values = {}
        # for segments in segments_list:
        #     values[segments] = {}

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                for segments in segments_list:
                    with self.subTest(variant=variant, path=path, segments=segments):
                        for _ in _TIME.measure_many(
                                '{}.{}.{}'.format(name, segments, variant), 1000):
                            value = tested_function(segments)
                        if segments >= 17:
                            self.assertAlmostEqual(value, np.pi, places=5)
                        elif segments > 10:
                            self.assertAlmostEqual(value, np.pi, places=6)
                        elif segments > 4:
                            self.assertAlmostEqual(value, np.pi, places=3)
                        else:
                            self.assertAlmostEqual(value, np.pi, places=0)
                        # values[segments][variant] = value
                        # _LOG.warning('timing: %s, value=%f', timer, value)

        for segments in segments_list:
            timings_name = '.'.join([__name__, name, str(segments)])
            summary = timing.query_cache(timings_name).summary
            _LOG.info('%s', summary)
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        # for segments in segments_list:
        #    vals = list(values[segments].values())
        #    for val in vals:
        #        self.assertEqual(vals[0], val)

    def test_copy_array(self):
        name = 'copy_array'
        variants = {
            'py': EXAMPLES_ROOTS['python3'].joinpath(name + '.py'),
            'f95': F2PyCompiler().compile_file(EXAMPLES_ROOTS['f95'].joinpath(name + '.f90'))}
        variants['py_numba'] = variants['py']
        variants['numpy'] = variants['py']
        if platform.system() == 'Linux':
            # variants['cpp'] = CppSwigCompiler().compile_file(
            #     EXAMPLES_ROOTS['cpp14'].joinpath(name + '.cpp'))
            # variants['py_to_cpp'] = AutoTranspiler(
            #     Language.find('Python 3'), Language.find('C++14')).transpile_file(variants['py'])
            pass
        # variants['py_to_f95'] = AutoTranspiler(
        #     Language.find('Python'), Language.find('Fortran 95')).transpile_file(variants['py'])

        transforms = {'py_numba': numba.jit, 'numpy': lambda _: np.copy}

        arrays = [np.array(np.random.random_sample((array_size,)), dtype=np.double)
                  for array_size in range(1024, 1024 * 64 + 1, 1024 * 4)]

        binder = Binder()
        for variant, path in variants.items():
            with binder.temporarily_bind(path) as binding:
                tested_function = getattr(binding, name)
                if variant in transforms:
                    tested_function = transforms[variant](tested_function)
                for array in arrays:
                    with self.subTest(variant=variant, path=path, array_size=array.size):
                        # with _TIME.measure('{}.{}.{}'.format(name, segments, variant)):
                        for _ in _TIME.measure_many(
                                '{}.{}.{}'.format(name, array.size, variant), 50):
                            array_copy = tested_function(array)
                        self.assertListEqual(array.tolist(), array_copy.tolist())

        for array in arrays:
            timings_name = '.'.join([__name__, name, str(array.size)])
            summary = timing.query_cache(timings_name).summary
            _LOG.info('%s', summary)
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

    def test_heavy_compute(self):
        kernel_name = 'heavy_compute'
        input_path = EXAMPLES_ROOTS['python3'].joinpath(kernel_name + '.py')

        # translator = AutoTranslator(Language.find('Python'), Language.find('Fortran'))
        # self.assertIsNotNone(translator)
        # reader = CodeReader()

        # with tempfile.NamedTemporaryFile(suffix='.f90', delete=False) as output_file:
        #     # TO DO: this leaves garbage behind in /tmp/
        #     output_path = pathlib.Path(output_file.name)

        # translated_code = translator.translate(reader.read_file(input_path), input_path)
        # , output_path, output_dir
        # print(translated_code)
        writer = CodeWriter('.f90')

        translated_code = '''
! inputSize

subroutine heavy_compute (inputData, inputSize, outputData)
  ! input arguments
  real*8, dimension(0:inputSize-1), intent(in) :: inputData
  integer, intent(in) :: inputSize

  ! output arguments
  real*8, dimension(0:(size(inputData) - 1)), intent(out) :: outputData

  ! local vars
  ! oh la la
  integer :: i
  integer :: n

  outputData = 0

  ! !$omp parallel do  ! 40x in gcc, 1x in pgi
  ! !$omp parallel do private(i) shared(inputData)  ! 40x in gcc, 1x in pgi
  ! !$omp parallel do private(i) shared(inputData, outputData)  ! 40x in gcc, 1x in pgi
  !$omp parallel do
  !$acc parallel loop
  do i = 0, (size(inputData) - 1)
    outputData(i) = 1
    do n = 0, (102400 - 1)
      outputData(i) = (outputData(i) / inputData(i))
    end do
    do n = 0, (102400 - 1)
      outputData(i) = (outputData(i) * inputData(i))
    end do
    do n = 0, (51200 - 1)
      outputData(i) = (outputData(i) / inputData(i))
    end do
    do n = 0, (51200 - 1)
      outputData(i) = (outputData(i) * inputData(i))
    end do
  end do
  !$omp end parallel do
  return
end subroutine heavy_compute
'''

        compilers = {name: F2PyCompiler(interface) for name, interface in {
            'gcc.serial': GfortranInterface(), 'gcc.openmp': GfortranInterface({'OpenMP'}),
            # GfortranInterface({'OpenACC'}),
            'pgi.serial': PgifortranInterface(), 'pgi.openmp': PgifortranInterface({'OpenMP'}),
            'pgi.openacc': PgifortranInterface({'OpenACC'})}.items()}
        binder = Binder()

        input_sizes = [pow(2, n) for n in range(4, 14)]  # (4, 11) for quick tests
        inputs = [np.linspace(1.0001, 1.0002, i, dtype=np.double)
                  for i in input_sizes]
        large_input_sizes = [pow(2, n) for n in range(14, 22)]  # 20  # (11, 14) for quick tests
        large_inputs = [np.linspace(1.0001, 1.0002, i, dtype=np.double)
                        for i in large_input_sizes]
        # for i in input_sizes:
        #    input_data = np.linspace(1.0001, 1.0002, i, dtype=np.double)
        for name, compiler in compilers.items():
            output_dir = make_f2py_tmp_folder(input_path)
            translated_path = output_dir.joinpath('{}.f90'.format(kernel_name))
            writer.write_file(translated_code, translated_path)

            compiled_path = compiler.compile(translated_code, translated_path, output_dir)
            with binder.temporarily_bind(compiled_path) as binding:
                inputs_ = itertools.chain(inputs, large_inputs) \
                    if name in {'gcc.openmp', 'pgi.openacc'} else inputs
                for input_data in inputs_:
                    input_size = np.size(input_data, 0)
                    for timer in _TIME.measure_many(
                            '.'.join([kernel_name, name, str(input_size)]), samples=3):
                        output_data = binding.heavy_compute(input_data, input_size)
                    _LOG.info('%s compiled with %s ran in %fs for input size %i',
                              kernel_name, name, timer.elapsed, input_size)
            # print(timing.query_cache('{}.compute.heavy_compute.{}'.format(__name__, 'gcc')))
            # exit()

        for name in compilers:
            timings_name = '.'.join([__name__, kernel_name, name])
            summary = timing.query_cache(timings_name).summary
            json_to_file(summary, PERFORMANCE_RESULTS_ROOT.joinpath(timings_name + '.json'))

        for name in compilers:
            comp, _, ver = name.partition('.')
            if ver == 'serial':
                continue
            baseline_summary = timing.query_cache(
                '.'.join([__name__, kernel_name, comp, 'serial'])).summary
            summary = timing.query_cache(
                '.'.join([__name__, kernel_name, name])).summary
            # import ipdb; ipdb.set_trace()
            speedups = {
                i: baseline_summary['{}'.format(i)]['median'] / summary['{}'.format(i)]['median']
                for i in input_sizes}
            _LOG.info('median speedups in %s of %s vs serial: %s', comp, ver, speedups)

        baseline_summary = timing.query_cache(
            '.'.join([__name__, kernel_name, 'gcc.openmp'])).summary
        summary = timing.query_cache(
            '.'.join([__name__, kernel_name, 'pgi.openacc'])).summary
        speedups = {
            i: baseline_summary['{}'.format(i)]['median'] / summary['{}'.format(i)]['median']
            for i in itertools.chain(input_sizes, large_input_sizes)}
        _LOG.info('median speedups of %s vs %s: %s', 'pgi.openacc', 'gcc.openmp', speedups)
