module m2
  use m3
  use m4
  implicit none
contains
  subroutine proc2
    print *, 'proc2'
    call proc3
    call proc4
    include 'i1.f90'
  end subroutine
end module
