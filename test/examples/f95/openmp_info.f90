!
subroutine openmp_info()

  use omp_lib

  integer :: omp_procs
  integer :: omp_max_threads
  integer :: omp_threads
  integer :: omp_thread
  integer :: omp_thread_limit
  integer :: omp_devices

  omp_procs = omp_get_num_procs()
  omp_max_threads = omp_get_max_threads()
  omp_threads = omp_get_num_threads()
  omp_thread = omp_get_thread_num()

  omp_thread_limit = omp_get_thread_limit()
  ! omp_get_default_device()
  omp_devices = omp_get_num_devices()
  ! omp_get_num_teams()
  ! omp_get_team_num()
  ! omp_is_initial_device()

end subroutine
