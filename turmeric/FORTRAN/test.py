import numpy as np
from scipy.linalg import lu
#################
import LINALG

d = 3
A = np.random.rand(d*d).reshape([d,d])
print(A)
b = np.arange(d)
print("RHS\n")
print(b)
print("\n")

LU, INDX, D, C = LINALG.ludcmp(A, A.shape[0])
SOL = LINALG.lubksb(LU, INDX,  b, n=d)
print("Fortran solution\n")
print(SOL)
print("Is singular?\n")
print(C)

print("Numpy solution\n")
print(np.linalg.solve(A, b))


