! calculate determinant of matrix
! use in DC estimator
recursive function determinant(a, n, permanent) result(accumulation)
  ! permanent -> 1 : compute permanent
  ! permanent -> -1 : compute determinant
  IMPLICIT NONE
  real(8), intent(in) :: A(n, n)
  integer, intent(in) :: n, permanent
  real(8) :: b(n-1, n-1)
  real(8) :: accumulation
  integer :: i, sgn

  if (n .eq. 1) then
    accumulation = a(1, 1)
  else
    accumulation = 0
    sgn = 1
    do i=1, n
      b(:, :(i-1)) = a(2:, :i-1)
      b(:, i:) = a(2:, i+1:)
      accumulation = accumulation + sgn * a(1,i) * determinant(b, n-1, permanent)
      sgn = sgn * permanent
    enddo
  endif
end function determinant
