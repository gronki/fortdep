module m1
  use m2
  implicit none
  interface
    module subroutine proc1
    end subroutine
  end interface
end module
