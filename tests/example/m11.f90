submodule (m1) m11
  use m3
  implicit none
contains
  subroutine proc1
    print *, 'proc1'
    call proc2
    call proc3
  end subroutine
end submodule
