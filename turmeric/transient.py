"""



"""

import numpy as np

from . import dc

from . import settings
from .FORTRAN.DC_SUBRS import gmin_mat
from .ODEsolvers import BE

import logging
from . import results

specs = {'tran':{'tokens':({
                          'label':'tstep',
                          'pos':0,
                          'type':float,
                          'needed':True,
                          'dest':'tstep',
                          'default':None
                         },
                         {
                          'label':'tstop',
                          'pos':1,
                          'type':float,
                          'needed':True,
                          'dest':'tstop',
                          'default':None
                         },
                         {
                          'label':'tstart',
                          'pos':None,
                          'type':float,
                          'needed':False,
                          'dest':'tstart',
                          'default':0
                         },
                         {
                          'label':'uic',
                          'pos':2,
                          'type':float,
                          'needed':False,
                          'dest':'uic',
                          'default':0
                         },
                         {
                          'label':'ic_label',
                          'pos':None,
                          'type':str,
                          'needed':False,
                          'dest':'x0',
                          'default':0
                         },
                         {
                          'label':'method',
                          'pos':None,
                          'type':str,
                          'needed':False,
                          'dest':'method',
                          'default':None
                         }
                        )
               }
           }
# CONFIG OPTIONS
# - Integration Method
config_integration = 'TRAP'
config_gmin = 1e-12
config_MAX_ITER = 20
config_hmin = 1e-20


def transient_analysis(circ, tstart, tstep, tstop, method=settings.default_integration_scheme, x0=None,
                       outfile="stdout", return_req_dict=None):   
    
    """
    
    """
    
    # setup integration method
    diff_slv = set_method(config_integration)
    
    # check params    
    if tstart > tstop:
        logging.critical("tstart > tstop")
        raise ValueError("Start value is greater than stop value - can't time travel")
    
    if tstep < 0 or tstart < 0 or tstop < 0:
        logging.critical("t-values are less than 0")
        raise ValueError("Bad t-value. Must be positive")

    locked_nodes = circ.get_locked_nodes()
    
    M, ZDC, D = get_reduced_system(circ)
    M_size = M.shape[0]
    NNODES = circ.get_nodes_number()
    x0 = format_estimate(x0, M_size)
    
    logging.info("Building Gmin matrix")

    Gmin_matrix = gmin_mat(config_gmin, M.shape[0], NNODES-1)
    sol = results.Solution(circ, None, sol_type='TRAN', extra_header='t')
    
    #       tpoint  x    dx
    buf = [(tstart, x0, None)]
    
    logging.info("Beginning transient")
    
    i = 0
    t = tstart
    
    while t < tstop:
        if i < diff_slv.rsteps:
            C1, C0 = BE.get_coefs((buf[i][1]), tstep)
        else:
            C1, C0 = diff_slv.get_coefs(buf, tstep)

        circ.gen_matrices(t)
        ZT = circ.ZT0[1:]
        

        x, error, solved, n_iter = dc.dc_solve(M=(M + C1 * D),
                                               ZDC=(ZDC + np.dot(D, C0) +ZT), circ=circ,
                                               Gmin=Gmin_matrix, x0=x0,
                                               time=(t + tstep),
                                               locked_nodes=locked_nodes,
                                               MAXIT=config_MAX_ITER)


        if solved:
            t += tstep          # update time step
            x0 = x              # update initial estimate
            i += 1              # increment
            row = [t]
            # now append computations
            row.extend(x.transpose().tolist()[0])
            # write to file
            sol.write_data(row)
            dxdt = np.multiply(C1, x) + C0
            buf.append((t, x, dxdt))
            #print(f"{t/tstop*100} %", flush=True)
            if len(buf) > diff_slv.rsteps:
                buf.pop(0)
                
            #
            #
            
        else:
            logging.error("Can't converge with step "+str(tstep)+".")
            logging.info("Reduce step or increase max iterations")
            solved = False
            break

    if solved:
        # return the solution object
        logging.info("Transient complete")
        return sol.as_dict(float)
    
    logging.info("Failed to solve")
    return None

def set_method(method='TRAP'):
    
    """
    Sets the integration scheme to be used in the transient simulation.
    
    Defaults to trapezoidal if no integration scheme is specified, or if
    the specified scheme is unsupported
    
    Parameters:
        method : String containing integration scheme name
    
    Returns:
        Integration scheme object
    """ 

    if method.upper() == 'TRAP':
        from .ODEsolvers import TRAP as m
    elif method.upper() == 'BDF2':
        from .ODEsolvers import BDF2 as m
    elif method.upper() == 'ADAMSM':
        from .ODEsolvers import ADAMSM as m
    else:
        logging.warning("Integration scheme unsupported\n \
                        Defaulting to trapezoidal...")
        from .ODEsolvers import trapezoidal as m
    
    return m

def get_reduced_system(circ):
    """
    Auxiliary function to set up the MNA equations for the transient simulation
    
    Parameters
    ----------
    circ : circuit object

    Returns
    -------
    M : reduced M0 matrix
    ZDC : reduced ZDC0 matrix
    D : reduced dynamic matrix

    """
    logging.debug("Getting and reducing MNA equations from circuit")
     
    M = circ.M0[1:, 1:]
    ZDC = circ.ZDC0[1:]
    
    logging.debug("Getting and reducing dynamic matrix D0 from circuit")
    # Once again, if Dynamic matrix has been generated for previous transient, we reuse
    D = circ.D0[1:, 1:]
    
    return (M, ZDC, D)

def format_estimate(x0, dim):
    """
    Auxiliary function to format the estimate provided by the DC operating point
    simulation

    Parameters
    ----------
    x0 : initial estimate
    dim : system dimensions

    Returns
    -------
    x0 : numpy array of the initial estimate

    """
    
    if x0 is None:
        logging.info("No initial solution provided... Not ideal")
        x0 = np.zeros((dim, 1))
    else:
        logging.info("Using provided x0")
        if isinstance(x0, dict):
            logging.info("Operating point solution provided as simulation result")
            x0 = [value for value in x0.values()]
            x0 = np.array(x0)
    
    logging.debug("Initial estimate is...")
    logging.debug(x0)
    
    return x0