import numpy as np
from scipy.linalg import lu
#################
import LINALG
import SVD

d = 3
S = np.array(([3.0,6], [1, 2]))
A = np.random.rand(d*d).reshape([d,d])
print(A)
b = np.arange(d)
print("RHS\n")
print(b)
print("\n")

LU, INDX, D, C = LINALG.ludcmp(A, A.shape[0])
SOL = LINALG.lubksb(LU, INDX,  b, n=d)
print("Printing RHS")
print(b)
print("Fortran solution\n")
print(SOL)
print("Is singular?\n")
print(C)

print("Numpy solution\n")
print(np.linalg.solve(A, b))

print("Testing for singularity...")
LU, INDX, D, C = LINALG.ludcmp(S, S.shape[0])
print("Is singular?\n")
print(C)

print("Numpy solution\n")
print(np.linalg.solve(S, np.zeros(S.shape[0])))

