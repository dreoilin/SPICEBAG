"""

Backward Euler (BE) module

"""

def get_coefs(x, step):
    
    """
    step [float]: current timestep
    x [float array]: system state at t = n
    
    dx_{n+1} = C1 * x_{n+1} + C0
    
    Function creates constants C1 and C0 and returns in a tuple
    
    C1 is used to create the M matrix contribution of the D matrix
    at time t=t_{n+1}
    
    C0 is used in the calculation of the state derivative once the state
    has been found
    
    """
    C1 = 1./step
    C0 = (-1./step)*x

    return (C1, C0)