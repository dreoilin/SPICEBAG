"""

A lightweight module containing any numerical algorithms without a home

"""
import logging

def newtonRaphson(f, x0, df=None, args=(), tol=1e-10, MAXITERS=500):
    
    """
    Single variable Newton Raphson function
    
    Parameters:
        f  : callable, single variable function
              with optional params f(x, *params)
        x0 : initial estimate of the function root
        df : callable, function derivative wrt x
        args : tuple containing optional args to be
                unpacked into f and df
        tol : tolerance of the root
        MAXITERS : maximum allowable amount of newton steps
    
    Output:
        x : root of equation
    
    """
    # first newton step
    x = x0 - (f(x0, *args))/(df(x0, *args))
    
    iters = 0
    while (abs(f(x, *args)) > tol):
        iters += 1
        x = x - (f(x0, *args))/(df(x0, *args))
        if (iters < MAXITERS):
            logging.critical("newtonRaphson(): newton method did not converge")
            raise ValueError
         
    return x
