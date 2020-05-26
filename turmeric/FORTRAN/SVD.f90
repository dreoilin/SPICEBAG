 subroutine svdcmp(a, m, n, mp, np, v, w)
    IMPLICIT NONE
! given matrix A(1;m, 1:n) with physical dimensions
! mp x np, routine computes the singular value dcmp
!            A = U * W * V.transpose

    INTEGER, intent(in) :: m, mp, n, np
    INTEGER :: NMAX
    REAL(8), intent(inout) :: a(mp, np)
!f2py intent(in, out) :: A
    REAL(8), intent(inout) :: v(np,np), w(np)
!f2py intent(in, out) :: v, w
    PARAMETER (NMAX=500) ! maximum value of n

    INTEGER :: i, its, j, jj, k, l, nm
    REAL(8) :: anorm, c, f, g, h, s, scale, x, y, z, rv1(NMAX)
    g=0.0
    scale=0.0
    anorm=0.0

    ! householder reduction to bidiagonal form
    do i=1,N
        l=i+1
        rv1(i)=scale*g
        g=0.0
        s=0.0
        scale=0.0
        if(i.le.m)then
            do k=i,m
                scale=scale+abs(a(k,i))
            enddo
            if(scale.ne.0.0)then
                do k=i,m
                    a(k,i)=a(k,i)/scale
                    s=s+a(k,i)*a(k,i)
                enddo
                f=a(i,i)
                g=-sign(sqrt(s),f)
                h=f*g-s
                a(i,i)=f-g
                do j=l,n
                    s = 0.0
                    do k=i,m
                        s=s+a(k,i)*a(k,j)
                    enddo
                    f=s/h
                    do k=i,m
                        a(k,j)=a(k,j)+f*a(k,i)
                    enddo
                enddo
                do k=i,m
                    a(k,i)=scale*a(k,i)
                enddo
            endif
        endif
        w(i)=scale*g
        g=0.0
        s=0.0
        scale=0.0
        if((i.le.m).and.(i.ne.n))then
            do k=l,n
                scale=scale+abs(a(i,k))
            enddo
            if(scale.ne.0.0) then
                do k=l,n
                  a(i,k)=a(i,k)/scale
                  s=s+a(i,k)*a(i,k)
                enddo
                f=a(i,l)
                g=-sign(sqrt(s),f)
                h=f*g-s
                a(i,l)=f-g
                do k=l,n
                    rv1(k)=a(i,k)/h
                enddo
                do j=l,m
                    s=0.0
                    do k=l,n
                        s=s+a(j,k)*a(i,k)
                    enddo
                    do k=l,n
                        a(j,k)=a(j,k)+s*rv1(k)
                    enddo
                enddo
                do k=1,n
                    a(i,k)=scale*a(i,k)
                enddo
            endif
        endif
        anorm=max(anorm,(abs(w(i))+abs(rv1(i))))
    enddo
    do i=n,1,-1
        if(i.lt.n)then
            if(g.ne.0.0)then
                do j=1,n
                    v(j,i)=(a(i,j)/a(i,l))/g
                enddo
                do j=l,n
                    s=0.0
                    do k=l,n
                        s=s+a(i,k)*v(k,j)
                    enddo
                    do k=l,n
                        v(k,j)=v(k,j)+s*v(k,i)
                    enddo
                enddo
            endif
            do j=l,n
                v(i,j)=0.0
                v(j,i)=0.0
            enddo
        endif
        v(i,i)=1.0
        g=rv1(i)
        l=i
    enddo
    do i=min(m,n),1,-1
        l=i+1
        g=w(i)
        do j=1,n
            a(i,j)=0.0
        enddo
        if(g.ne.0.0)then
            g=1.0/g
            do j=l,n
                s=0.0
                do k=l,m
                    s=s+a(k,i)*a(k,j)
                enddo
                f=(s/a(i,i))*g
                do k=i,m
                    a(k,j)=a(k,j)+f*a(k,i)
                enddo
            enddo
            do j=i,m
                a(j,i)=a(j,i)*g
            enddo
        else
            do j=i,m
                a(j,i)=0.0
            enddo
        endif
        a(i,i)=a(i,i)+1.0
    enddo
    do k=n,1,-1
        do its=1,30
            do l=k,1,-1
                nm=l-1
                if((abs(rv1(l))+anorm).eq.anorm) goto 2
                if((abs(w(nm))+anorm).eq.anorm) goto 1
            enddo
1           c=0.0
            s=1.0
            do i=l,k
                f=s*rv1(i)
                rv1(i)=c*rv1(i)
                if((abs(f)+anorm).eq.anorm) goto 2
                g=w(i)
                h=pythag(f,g)
                w(i)=h
                h=1.0/h
                c=(g*h)
                s=-(f*h)
                do j=1,m
                    y=a(j,nm)
                    z=a(j,i)
                    a(j,nm)=(y*c)+(z*s)
                    a(j,i)=-(y*s)+(z*c)
                enddo
            enddo
2           z=w(k)
            if(l.eq.k) then
                if(z.lt.0.0) then
                    w(k)=-z
                    do j=1,n
                        v(j,k)=-v(j,k)
                    enddo
                endif
                goto 3
            endif
            x=w(l)
            nm=k-1
            y=w(nm)
            g=rv1(nm)
            h=rv1(k)
            f=((y-z)*(y+z)+(g-h)*(g+h))/(2.0*h*y)
            g=pythag(f,1D0)
            f=((x-z)*(x+z)+h*((y/(f+sign(g,f)))-h))/x
            c=1.0
            s=1.0
            do j=l,nm
                i=j+1
                g=rv1(i)
                y=w(i)
                h=s*g
                g=c*g
                z=pythag(f,h)
                rv1(j)=z
                c=f/z
                s=h/z
                f= (x*c)+(g*s)
                g=-(x*s)+(g*c)
                h=y*s
                y=y*c
                do jj=1,n
                    x=v(jj,j)
                    z=v(jj,i)
                    v(jj,j)=(x*c)+(z*s)
                    v(jj, i)=-(x*s)+(z*c)
                enddo
                z=pythag(f,h)
                w(j)=z
                if(z.ne.0.0)then
                    z=1.0/z
                    c=f*z
                    s=h*z
                endif
                f=(c*g)+(s*y)
                x=-(s*g)+(c*y)
                do jj=1,m
                    y=a(jj,j)
                    z=a(jj,i)
                    a(jj,j)=(y*c) + (z*s)
                    a(jj,i)=-(y*s)+(z*c)
                enddo
            enddo
            rv1(l)=0.0
            rv1(k)=f
            w(k)=x
        enddo
 3      continue
    enddo
    return

    contains
    REAL(8) FUNCTION pythag(A,B)
    IMPLICIT NONE
! computes (a^2 + b^2)^(1/2) without under or overflow
    REAL(8), intent(in):: A
    REAL(8), intent(in) :: B

    REAL(8) :: absa, absb
    absa= abs(A)
    absb=abs(B)
    if(absa.gt.absb)then
        pythag=absa*sqrt(1.+(absb/absa)**2)
    else
        if(absb.eq.0.)then 
            pythag=0.0
	else
	    pythag=absb*sqrt(1.+(absa/absb)**2)
	endif
    endif
    return
    END FUNCTION pythag

end subroutine svdcmp

subroutine svbksb(u, w, v, m, n, mp, np, b, x)
    IMPLICIT NONE
    INTEGER, intent(in) :: m, mp, n, np
    REAL(8), intent(in) :: b(mp),u(mp,np), v(np,np), w(np)
    REAL(8), intent(inout) :: x(np)
!f2py intent(in, out) :: X
    INTEGER :: NMAX
    PARAMETER(NMAX=500)

    INTEGER :: i, j, jj
    REAL(8) :: s, tmp(NMAX)

! calculate U.transpose B
    do j=1,n
        s=0.0
        if(w(j).ne.0.)then
            do i=1,m
                s=s+u(i,j)*b(i)
            enddo
            s=s/w(j)
        endif
        tmp(j)=s
    enddo
    do j=1,n
        s=0.0
        do jj=1,n
            s=s+v(j,jj)*tmp(jj)
        enddo
        x(j)=s
    enddo
    return
END SUBROUTINE svbksb
