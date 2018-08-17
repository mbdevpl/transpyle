
subroutine dim_loop(i, j, k, FlatTilde, U, )

  integer, intent(in) :: i, j, k
  FlatTilde
  real, pointer, dimension(:,:,:,:) :: U
  integer :: dir ! rename

  do dir=1,NDIM
     select case (dir)
     case (DIR_X)
        dp1   = (U(PRES_VAR,i+1,j,k)-U(PRES_VAR,i-1,j,k))
        dp2   = (U(PRES_VAR,i+2,j,k)-U(PRES_VAR,i-2,j,k))
        dv1   =  U(VELX_VAR,i+1,j,k)-U(VELX_VAR,i-1,j,k)
        presL =  U(PRES_VAR,i-1,j,k)
        presR =  U(PRES_VAR,i+1,j,k)
  #if NDIM > 1
     case (DIR_Y)
        dp1   = (U(PRES_VAR,i,j+1,k)-U(PRES_VAR,i,j-1,k))
        dp2   = (U(PRES_VAR,i,j+2,k)-U(PRES_VAR,i,j-2,k))
        dv1   =  U(VELY_VAR,i,j+1,k)-U(VELY_VAR,i,j-1,k)
        presL =  U(PRES_VAR,i,j-1,k)
        presR =  U(PRES_VAR,i,j+1,k)
  #if NDIM > 2
     case (DIR_Z)
        dp1   = (U(PRES_VAR,i,j,k+1)-U(PRES_VAR,i,j,k-1))
        dp2   = (U(PRES_VAR,i,j,k+2)-U(PRES_VAR,i,j,k-2))
        dv1   =  U(VELZ_VAR,i,j,k+1)-U(VELZ_VAR,i,j,k-1)
        presL =  U(PRES_VAR,i,j,k-1)
        presR =  U(PRES_VAR,i,j,k+1)
  #endif
  #endif
     end select

     if (abs(dp2) > 1.e-15) then
        Sp = dp1/dp2 - 0.75
     else
        Sp = 0.
     endif

     FlatTilde(dir,i,j,k) = max(0.0, min(1.0,10.0*Sp))
     if ((abs(dp1)/min(presL,presR) < 1./3.) .or. dv1 > 0. ) then
        FlatTilde(dir,i,j,k) = 0.
     endif

  enddo

end subroutine
