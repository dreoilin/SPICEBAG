#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian
"""

import numpy as np

from . import dc
from . import options
from .FORTRAN.DC_SUBRS import gmin_mat

import logging
from . import results

# basic integration method
from . import BEuler as BE

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


def set_method(method='TRAP'):
    
    if method.upper() == 'TRAP':
        from . import trapezoidal as diff_slv
    #elif method.upper() == ''
    else:
        logging.warning("Integration scheme unsupported\n \
                        Defaulting to trapezoidal...")
        from . import trapezoidal as diff_slv
    
    
def transient_analysis(circ, tstart, tstep, tstop, x0=None, method=None,
                       outfile="stdout", return_req_dict=None):   
    
    """
    
    """
    
    # setup integration method
    set_method(config_integration)
    
    # check params    
    if tstart > tstop:
        logging.critical("tstart > tstop")
        raise ValueError("Start value is greater than stop value - can't time travel")
    if tstep < 0 or tstart < 0 or tstop < 0:
        logging.critical("t-values are less than 0")
        raise ValueError("Bad t-value. Must be positive")

    locked_nodes = circ.get_locked_nodes()
    
    # matrix gen
    logging.info("Getting and reducing MNA equations from circuit")
    # MNA GEN: if an OP has already been completed, these matrices are already available
    
    M = circ.M0[1:, 1:]
    ZDC = circ.ZDC0[1:]
    M_size = M.shape[0]
    
    logging.info("Getting and reducing dynamic matrix D0 from circuit")
    # Once again, if Dynamic matrix has been generated for previous transient, we reuse
    D = circ.D0[1:, 1:]
    
    # setup the initial values to start the iteration:
    NNODES = circ.get_nodes_number()
    
    # good old gmin, take away a node : reduced
    logging.info("Building Gmin matrix")
    Gmin_matrix = gmin_mat(options.gmin, M.shape[0], NNODES-1)
    
    # We need an initial estimate to begin the transient
    if x0 is None:
        logging.info("No initial solution provided... Not ideal")
        x0 = np.zeros((M_size, 1))
    else:
        logging.info("Using provided x0")
        if isinstance(x0, dict):
            logging.info("Operating point solution provided")
            x0 = [value for value in x0.values()]
            x0 = np.array(x0)
     
    logging.info("Initial estimate is...")
    
    # we store the system state and derivative at a point t inside a buffer
    buf = [(tstart, x0, None)]
    
    # set up a solution object
    sol = results.Solution(circ, outfile, sol_type='TRAN', extra_header='t')
    
    logging.info("Beginning transient")
    i = 0
    t = tstart
    
    # cant load up whole list into memory so have to use while and increment
    while t < tstop:
        if i < 1:
            # for the first iteration we need to use implicit euler
            C1, C0 = BE.get_coefs((buf[0][1]), tstep)
        else:
            C1, C0 = diff_slv.get_coefs(buf, tstep)
        
        
        
        circ.gen_matrices(t)
        # retrieve ZAC and add to DC component
        ZT = circ.ZT0[1:]
        
        
        x, error, solved, n_iter = dc.dc_solve(
                                                     M=(M + C1 * D),
                                                     ZDC=(ZDC + np.dot(D, C0) +ZT), circ=circ,
                                                     Gmin=Gmin_matrix, x0=x0,
                                                     time=(t + tstep),
                                                     locked_nodes=locked_nodes,
                                                     MAXIT=options.transient_max_nr_iter
                                                     )

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
            print(f"{t/tstop*100} %", flush=True)
            buf.pop(0)
        else:
            logging.error("Can't converge with step "+str(tstep)+".")
            logging.error("Try setting --t-max-nr to a higher value or set step to a lower one.")
            solved = False
            break

    if solved:
        # return the solution object
        return sol.as_dict(float)
    
    return None

