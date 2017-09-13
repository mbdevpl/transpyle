!     Unclassified/Unrestricted Distribution
!     
!     UCRL-CODE-155977
!     Miranda FORTRAN I/O test code, Version 1.0
!     Author(s): B. Cabot
!     
!     OCEC:  This is OCEC-138
!     
!     Your code has been given an Unrestricted Distribution.
!     
!     
!     This work was produced at the University of California, Lawrence Livermore 
!     National Laboratory (UC LLNL) under contract no. W-7405-ENG-48 (Contract 48) 
!     between the U.S. Department of Energy (DOE) and The Regents of the University of 
!     California (University) for the operation of UC LLNL. The rights of the Federal 
!     Government are reserved under Contract 48 subject to the restrictions agreed upon 
!     by the DOE and University as allowed under DOE Acquisition Letter 97-1.
!     
!     
!     
!     DISCLAIMER
!     
!     This work was prepared as an account of work sponsored by an agency of the United 
!     States Government. Neither the United States Government nor the University of 
!     California nor any of their employees, makes any warranty, express or implied, or 
!     assumes any liability or responsibility for the accuracy, completeness, or 
!     usefulness of any information, apparatus, product, or process disclosed, or 
!     represents that its use would not infringe privately-owned rights.  Reference 
!     herein to any specific commercial products, process, or service by trade name, 
!     trademark, manufacturer or otherwise does not necessarily constitute or imply its 
!     endorsement, recommendation, or favoring by the United States Government or the 
!     University of California. The views and opinions of authors expressed herein do 
!     not necessarily state or reflect those of the United States Government or the 
!     University of California, and shall not be used for advertising or product 
!     endorsement purposes.
!     
!     
!     NOTIFICATION OF COMMERCIAL USE
!     
!     Commercialization of this product is prohibited without notifying the Department 
!     of Energy (DOE) or Lawrence Livermore National Laboratory (LLNL).

      program miranda_io

      implicit none

      character*1024 :: basefname = "miranda_io.out"
      character*1024 :: fname, file_suffix, home

      integer, parameter :: ni=24, nj=30, nk=1680
      integer, parameter :: loopparm=100, shiftparm=4

      integer(kind=8), dimension(ni,nj,nk) :: W1, R1, W2, R2
      integer(kind=8), dimension(ni,nj,nk,2) :: W3, R3, W4, R4
      integer(kind=8), dimension(ni,nj,nk,4) :: W5, R5, W6, R6
      integer, dimension(4) :: mloc

      integer :: ierr, errors, all_errors, nprocs, mynod, ios
      integer :: i,j,k,l,ijk,loop

      integer :: writeunit, readunit
      integer(kind=8) :: ishift, nodeoff, wvalue, rvalue

      include 'mpif.h'

      call MPI_INIT(ierr)
      call MPI_COMM_SIZE(MPI_COMM_WORLD, nprocs, ierr)
      call MPI_COMM_RANK(MPI_COMM_WORLD, mynod, ierr)

!     check environment for file name, then broadcast from root task
      if (mynod == 0) then
        call getenv('MIRANDA_IO_FNAME', value=home)
        if (trim(home) /= '') then
          basefname = trim(home)
        endif
      endif
      call MPI_BCAST(basefname, 1024, MPI_CHAR, 0, MPI_COMM_WORLD, ierr);

      if( mynod == 0 ) then
        print *, 'Fortran I/O test emulating Bill Cabots code and bz4410'
        print *, '6 mixed arrays of int*8 written by 1 write()'
        print *, 'base dimensions are IJK= ', ni,nj,nk
        print *, 'The test will execute ', loopparm, 'iterations'
        print *, 'For read your neighbor, the shift is ', shiftparm, 'tasks'
        print *, 'node(task reading) is node(task writing) + shift'
        print *, 'After reading back the arrays they are examined, and'
        print *, 'any discrepancies reported.'
        print *, ''
        print *, 'Writing to:  ', trim(basefname), '.*'
      endif

      nodeoff=2**21
      do loop = 1,loopparm

        forall(i=1:ni,j=1:nj,k=1:nk) W1(i,j,k) = nodeoff*mynod+i+ni*(j-1+nj*(k-1))
        W2 = W1
        forall(i=1:ni,j=1:nj,k=1:nk,l=1:2) W3(i,j,k,l) = nodeoff*mynod+i+ni*(j-1+nj*(k-1+nk*(l-1)))
        W4 = W3
        forall(i=1:ni,j=1:nj,k=1:nk,l=1:4) W5(i,j,k,l) = nodeoff*mynod+i+ni*(j-1+nj*(k-1+nk*(l-1)))
        W6 = W5

        writeunit = mynod+10000
        write(file_suffix, '(i5.5)') writeunit
        fname = trim(basefname) // '.' // trim(file_suffix)
        open(unit=writeunit,file=fname,form='unformatted',action='write')
        write(writeunit,iostat=ios) W5,W1,W2,W3(:,:,:,1),W6,W4(:,:,:,1)
        close(writeunit)

        call MPI_BARRIER(MPI_COMM_WORLD, ierr)

        ishift = shiftparm
        readunit = mynod + shiftparm
        if (readunit >= nprocs) then
          readunit = readunit - nprocs
          ishift = ishift - nprocs
        endif
        readunit = readunit+10000
        ishift = ishift * nodeoff

        R1 = 0
        R2 = 0
        R3 = 0
        R4 = 0
        R5 = 0
        R6 = 0

        write(file_suffix, '(i5.5)') readunit
        fname = trim(basefname) // '.' // trim(file_suffix)
        open(unit=readunit,file=fname,form='unformatted',action='read')
        read(readunit,iostat=ios) R5,R1,R2,R3(:,:,:,1),R6,R4(:,:,:,1)
        close(readunit)

        errors = 0
        ierr = count( R1-W1 /= ishift )
        if( ierr > 0 ) then
          print *, 'Error1 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc(1:3) = maxloc(abs(R1-W1))
	  wvalue = W1(mloc(1),mloc(2),mloc(3))+ishift
	  rvalue = R1(mloc(1),mloc(2),mloc(3))
          print *, 'Maximum error at ', mloc(1:3),' write ',wvalue,' ; read ',rvalue
        endif
        ierr = count( R2-W2 /= ishift )
        if( ierr > 0 ) then
          print *, 'Error2 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc(1:3) = maxloc(abs(R2-W2))
	  wvalue = W2(mloc(1),mloc(2),mloc(3))+ishift
	  rvalue = R2(mloc(1),mloc(2),mloc(3))
          print *, 'Maximum error at (', mloc(1:3),'); write ',wvalue,' ; read ',rvalue
        endif
        ierr = count( R3(:,:,:,1)-W3(:,:,:,1) /= ishift )
        if( ierr > 0 ) then
          print *, 'Error3 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc(1:3) = maxloc(abs(R3(:,:,:,1)-W3(:,:,:,1)))
	  wvalue = W3(mloc(1),mloc(2),mloc(3),1)+ishift
	  rvalue = R3(mloc(1),mloc(2),mloc(3),1)
          print *, 'Maximum error at (', mloc(1:3),'); write ',wvalue,' ; read ',rvalue
        endif
        ierr = count( R4(:,:,:,1)-W4(:,:,:,1) /= ishift )
        if( ierr > 0 ) then
          print *, 'Error4 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc(1:3) = maxloc(abs(R4(:,:,:,1)-W4(:,:,:,1)))
	  wvalue = W4(mloc(1),mloc(2),mloc(3),1)+ishift
	  rvalue = R4(mloc(1),mloc(2),mloc(3),1)
          print *, 'Maximum error at (', mloc(1:3),'); write ',wvalue,' ; read ',rvalue
        endif
        ierr = count( R5-W5 /= ishift )
        if( ierr > 0 ) then
          print *, 'Error5 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc = maxloc(abs(R5-W5))
	  wvalue = W5(mloc(1),mloc(2),mloc(3),mloc(4))+ishift
	  rvalue = R5(mloc(1),mloc(2),mloc(3),mloc(4))
          print *, 'Maximum error at (', mloc,'); write ',wvalue,' ; read ',rvalue
        endif
        ierr = count( R6-W6 /= ishift )
        if( ierr > 0 ) then
          print *, 'Error6 on task ',mynod,'at ',ierr,' points reading ',readunit - 10000
          errors = errors + ierr
          mloc = maxloc(abs(R6-W6))
	  wvalue = W6(mloc(1),mloc(2),mloc(3),mloc(4))+ishift
	  rvalue = R6(mloc(1),mloc(2),mloc(3),mloc(4))
          print *, 'Maximum error at (', mloc,'); write ',wvalue,' ; read ',rvalue
        endif

        call MPI_Allreduce(errors,all_errors,1,MPI_INTEGER,MPI_SUM,MPI_COMM_WORLD,ierr)
!rmh        if( all_errors > 0 ) exit
        if( all_errors > 0 ) call exit (1)

!       if( errors > 0 ) then
!          call MPI_Abort(MPI_COMM_WORLD,1,ierr)
!          stop
!       endif

        if( mynod == 0 ) print *, 'Iteration = ',loop,' completed.'

      end do ! loop

      call MPI_FINALIZE(ierr)

      end program miranda_io
