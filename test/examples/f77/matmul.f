        function intmatmul(limit, width, height)

        integer, intent(in) :: limit
        integer, intent(in) :: width
        integer, intent(in) :: height

        integer :: max_width, max_height, max_input, max_output

        parameter (max_width = 1024, max_height = 1024)
        parameter (max_input = max_width * max_height)
        parameter (max_output = max_height * max_height)

        integer :: a(max_width * max_height)
        integer :: b(max_height * max_width)
        integer :: c(max_height * max_height)

        integer :: n, y, i, x

        integer :: intmatmul

        data a /max_input * 1/
        data b /max_input * 1/
        data c /max_output * 0/

        do n = 1, limit
            c = 0
            do y = 1, height
                do i = 1, width
                    do x = 1, height
                        c((y - 1) * height + x) =
     +                      c((y - 1) * height + x) +
     +                      a((y - 1) * width + i) *
     +                      b((i - 1) * height + x)
                    end do
                end do
            end do
        end do

        if (limit .gt. 0) then
            do y = 1, height
                do x = 1, height
                    if (c((y - 1) * height + x) .ne. height) then
                        print '(I0, '' - error at '', I0, '' x '', I0)',
     +                      c((y - 1) * height + x), x, y
                        intmatmul = 2
                        return
                    end if
                end do
            end do
        end if

        intmatmul = 0

        end function intmatmul

        program main

        implicit none
        integer :: fileId
        integer :: limit, width, height

        integer :: intmatmul
        external intmatmul
        integer :: returncode

        parameter (fileId = 20)

        limit = 0
        width = 0
        height = 0

        open(fileId, file='res/input.txt', status='OLD')
        read(fileId, fmt='(I8,I8,I8)') limit, width, height
        close(fileId, status='KEEP')

        if (limit .lt. 0 .or. width .eq. 0 .or. height .eq. 0) then
            stop 1
        end if

C        print "(I0, ' times ', I0, ' x ', I0)", limit, width, height

        returncode = intmatmul(limit, width, height)

        if (returncode .ne. 0) then
            stop 2
        end if

        end program main
