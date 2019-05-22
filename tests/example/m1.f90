module m1
  use m2
  use m3
  implicit none
  interface
    module subroutine proc1
    end subroutine
  end interface
end module
