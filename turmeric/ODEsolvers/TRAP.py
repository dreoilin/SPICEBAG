"""
Trapezoidal integration scheme

Contains the required steps for a trapezoidal step
and a method to compute the coefficients for said step

"""


# required number of steps
rsteps = 1

def get_coefs(buf, step):
    """
    Compute the coefficients for a trapezoidal step
    
    Reuires:
        dxdt_n  : derivative at current step
        x_n     : state at current step
    Returns:
        Coefficients C1 and C0 used to compute conductances and current
        contibutions in the companion model representation
        
    """
    if len(buf[0]) != 3:
        raise ValueError('trapezoidal->get_coefs(): Badly formed array passed')
    
    # check if appropriate values 
    # method needs x(n) dx(n)/dt
    if buf[0][1] is None or buf[0][2] is None:
        raise ValueError('trapezoidal->get_coefs(): trap method requires state and derivative at current timestep')
    
    C1 = 2.0 / step
    C0 = -1.0 * (2.0 / step * buf[0][1] + buf[0][2])

    return (C1, C0)

