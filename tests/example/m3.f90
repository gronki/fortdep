module m3
  implicit none
contains
  subroutine proc3
    print *, 'proc3'
  end subroutine
end module

module m4
  use m3
  implicit none
contains
  subroutine proc4
    print *, 'proc4'
    call proc3
    include 'i1.f90'
    include 'i2.f90'
  end subroutine
end module
