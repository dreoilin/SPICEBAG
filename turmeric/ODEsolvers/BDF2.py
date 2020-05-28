"""
Backward Differentiation Order 2 (BDF2)

Contains the required steps for a BDF2 step
and a method to compute the coefficients for said step

"""

rsteps = 2


def get_coefs(buf, step):
    
    """
    Compute the coefficients for a BDF2 step
    
    Reuires:
        x_{n-1} : state at previous step
        x_n     : state at current step
    Returns:
        Coefficients C1 and C0 used to compute conductances and current
        contibutions in the companion model representation
    """    
    
    if len(buf[0]) != 3:
        raise ValueError('BDF2->get_coefs(): Badly formed array passed')
    # check for x and dx values
    if buf[0][1] is None or buf[1][1] is None:
        raise ValueError('BDF2->get_coefs(): BDF2 requires state at current and previous timestep')
        
    C1 = step * (3/2)
    C0 = -((2/step)*buf[1][1] + 1/(2*step)*buf[0][1])
    
    return (C1, C0)