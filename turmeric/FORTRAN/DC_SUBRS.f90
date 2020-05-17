subroutine gmin_mat(G, GMIN, N, NNODES)
  implicit none

  INTEGER, intent(in) :: N      ! dim of MNA
  REAL(8), intent(in) :: GMIN   ! min conduct
  INTEGER, intent(in) :: NNODES ! num nodes in circuit
  REAL(8), intent(out) :: G(N, N) ! store G ,at
!f2py intent(out) G
  INTEGER :: i
  ! init matrix to [0]
  G = 0
  ! at each diagonal up until NNODES, assign gmin
  forall(i = 1:NNODES) G(i, i) = GMIN
end subroutine
