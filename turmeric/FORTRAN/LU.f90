 Subroutine LUDCMP(A,N,INDX,D,CODE)
! given N x N matrix A, routine replaces it with
! LU dcmp of rowwise permutation of itself

! INDX [INT: N x 1] : vector which stores row permutations
! D [INT] : records whether num row changes odd (-1) or even (1)
  IMPLICIT NONE
  INTEGER, PARAMETER :: NMAX=100
  Real(4), PARAMETER :: TINY=1.5E-16
 
  INTEGER, intent(in) :: N
  REAL(8), intent(inout) :: A(N,N)
  INTEGER, intent(out) :: CODE, D, INDX(N)
!f2py intent(in, out) :: A

  INTEGER I, J, K, IMAX
  REAL(8)  AMAX, DUM, SUM, VV(NMAX) ! VV store scaling of row

  D=1; CODE=0 ! no row changes: init D to 1

  DO I=1,N
    AMAX=0.d0
    DO J=1,N
      IF (DABS(A(I,J)).GT.AMAX) AMAX=DABS(A(I,J))
    END DO ! j loop
    IF(AMAX.LT.TINY) THEN
      CODE = 1
      RETURN
    END IF
    VV(I) = 1.d0 / AMAX ! save scaling
  END DO ! i loop

  DO J=1,N
   DO I=1,J-1
      SUM = A(I,J)
      DO K=1,I-1
        SUM = SUM - A(I,K)*A(K,J) 
      END DO ! k loop
      A(I,J) = SUM
    END DO ! i loop
    AMAX = 0.d0
    DO I=J,N
      SUM = A(I,J)
      DO K=1,J-1
        SUM = SUM - A(I,K)*A(K,J) 
      END DO ! k loop
      A(I,J) = SUM
      DUM = VV(I)*DABS(SUM)
      IF(DUM.GE.AMAX) THEN
        IMAX = I
        AMAX = DUM
      END IF
    END DO ! i loop  
   
    IF(J.NE.IMAX) THEN
     DO K=1,N
        DUM = A(IMAX,K)
        A(IMAX,K) = A(J,K)
        A(J,K) = DUM
      END DO ! k loop
      D = -D
      VV(IMAX) = VV(J)
    END IF

    INDX(J) = IMAX
    IF(DABS(A(J,J)) < TINY) A(J,J) = TINY

    IF(J.NE.N) THEN
      DUM = 1.d0 / A(J,J)
      DO I=J+1,N
        A(I,J) = A(I,J)*DUM
      END DO ! i loop
    END IF 
  END DO ! j loop

  RETURN
  END subroutine LUDCMP

 Subroutine LUBKSB(A,N,INDX,B)
! computes the solution of the NxN LU decomposition
! with RHS B using backward substitution
 
 implicit none

 INTEGER, intent(in) :: N
 REAL(8) ::  SUM
 REAL(8), intent(in) :: A(N,N)
 INTEGER, intent(in) :: INDX(N)
 REAL(8), intent(inout) :: B(N)
!f2py intent(in, out) :: B
 
 INTEGER :: I, J, LL, II = 0

 DO I=1,N
   LL = INDX(I)
   SUM = B(LL)
   B(LL) = B(I)
   IF(II.NE.0) THEN
     DO J=II,I-1
       SUM = SUM - A(I,J)*B(J)
     END DO ! j loop
   ELSE IF(SUM.NE.0.d0) THEN
     II = I
   END IF
   B(I) = SUM
 END DO ! i loop

 DO I=N,1,-1
   SUM = B(I)
   IF(I < N) THEN
     DO J=I+1,N
       SUM = SUM - A(I,J)*B(J)
     END DO ! j loop
   END IF
   B(I) = SUM / A(I,I)

 END DO ! i loop

 RETURN
 END subroutine LUBKSB
