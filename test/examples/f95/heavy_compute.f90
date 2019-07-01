
subroutine heavy_compute (inputData, inputSize, outputData)
  ! input arguments
  real*8, dimension(0:inputSize-1), intent(in) :: inputData
  integer, intent(in) :: inputSize

  ! output arguments
  real*8, dimension(0:(size(inputData) - 1)), intent(out) :: outputData

  ! local vars
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
