"""

Backward Euler (beuler) module

Computes the coefficients for a backward euler step

"""

def get_coefs(x, step):
    
    C1 = 1./step
    C0 = (-1./step)*x

    return (C1, C0)