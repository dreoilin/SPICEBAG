#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Module to map a system of n equaitons with complex coefficients
to 2n equations with real-valued coefficients

"""
import numpy as np
from numpy.linalg import norm
import logging
from .FORTRAN.LU import ludcmp, lubksb

j = np.complex('j')    

def allocate_mats(n):
    """
    Given the dinemsion of an n x n 
    system of complex equations, allocates an
    A and RHS for a linear system derived from
    the complex
    """
    A = np.zeros((2*n, 2*n)) 
    b = np.zeros((2*n, 1))
    return (A, b)


def map_complex_to_linear(C):
    """
    Returns the mapping of a complex number to system of equations using
    https://hal-ens-lyon.archives-ouvertes.fr/ensl-00125369v2/document

    Parameters
    ----------
    C : complex number

    Returns
    -------
    numpy array containing matrix mapping

    """
    r = np.real(C)
    i = np.imag(C)
    
    return np.array(([[r, -i],
                      [i, r]]))

def populate_mats(A, b, A_c, b_c):
    """
    Populates an A and RHS matrix from a complex valued
    A and RHS.

    Parameters
    ----------
    A : numpy array
        2n x 2n zero matrix
    b : numpy array
        2n x 1 zero RHS
    A_c : numpy array (complex)
        n x n square matrix
    b_c : numpy array (complex)
        n x 1 RHS

    Returns
    -------
    A : numpy array
        containing linear mapping acc. to 
        map_complex_to_linear()
    b : numpy array
        mapped RHS

    """    
    n, m = A_c.shape
    for i in range(n):
        for j in range(m):
            A[(0+2*i):(2+2*i), (0+2*j):(2+2*j)] = map_complex_to_linear(A_c[i,j])
        b[i*2, 0] = np.real(b_c[i,0])
        b[i*2+1, 0] = np.imag(b_c[i,0])

    return (A, b)

def real_to_complex(x):
    """
    Takes the solution of a transformed complex system
    and maps it back to complex numbers. Returns an array
    of complex numbers.
    """
    n = int(x.shape[0]/2.0)
    x_c = np.zeros((n,1), dtype=complex)
    
    for i in range(n):
        x_c[i] = x[i*2] + j * x[i*2 + 1]
        
    return x_c

def solver(A_c, b_c):
    """
    

    Parameters
    ----------
    A_c : numpy array (complex)
        n x n matrix
    b_c : numpy array (complex)
        n x 1 RHS

    Returns
    -------
    x : numpy array
        n x 1 complex solution

    """
    
    (n, m) = A_c.shape
    
    if n != m:
        logging.error("complex_solve(): Matrix dimensions do not agree")
        raise ValueError
    if n != b_c.shape[0]:
        logging.error("complex_solve(): A and b matrix dimensions do not agree")
    
    A, b = allocate_mats(n)
    (A, b) = populate_mats(A, b, A_c, b_c)
    
    LU, INDX, _, C = ludcmp(A)
    if C == 1:
        logging.error("Singular matrix")
        raise ValueError
    
    x = lubksb(LU, INDX,  b)
    if norm(x) == np.nan:
        logging.error("Overflow error")
        raise OverflowError
    
    x_c = real_to_complex(x)
    
    return x_c
    