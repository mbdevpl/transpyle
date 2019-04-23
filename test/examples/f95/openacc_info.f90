
subroutine openacc_info()

  use openacc

  ! integer :: defined_macro
  integer :: acc_devices, acc_device, acc_device_type

  ! PGI_ACC_NOTIFY=3
  ! PGI_ACC_TIME=1
  ! defined_macro = _OPENACC

  acc_devices = acc_get_num_devices()
  acc_device = acc_get_device_num()
  acc_device_type = acc_get_device_type()

end subroutine
