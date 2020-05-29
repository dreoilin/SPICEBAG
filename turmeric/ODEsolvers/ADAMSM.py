"""

Adams Moulton integration scheme

Contains the required steps for an Adams Moulton step
and a method to compute the coefficients for said step

"""

rsteps = 2
 
def get_coefs(buf, step):
    
    """
    Compute the coefficients for an Adams Moulton step
    
    Reuires:
        x_n         : state at current step
        dx_n/dt     : derivative at current step
        dx_{n-1}/dt : derivative at previous step
    Returns:
        Coefficients C1 and C0 used to compute conductances and current
        contibutions in the companion model representation 
    
    """
    # check if appropriate values 
    # our method needs x(n) dx(n)/dt
    if len(buf[0]) != 3:
        raise ValueError('ADAMSM->get_coefs(): Badly formed array passed')
    # check for x and dx values
    if buf[0][2] is None or buf[1][1] is None or buf[1][2] is None:
        raise ValueError('ADAMSM->get_coefs(): method requires current state \
                         current derivative and derivative at previous time step')
    
    C1 = 12/(5 * step)
    C0 = -12/(5*step)*buf[1][1] - 8/5 * buf[1][2] + 1/5 * buf[0][2]
    
    return (C1, C0)