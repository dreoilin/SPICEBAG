#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import logging

from . import results
from . import complex_solve

SWEEP_LOG = "LOG"
SWEEP_LIN = "LIN"

specs = {'ac': {'tokens': ({
                           'label': 'type',
                           'pos': 0,
                           'type': str,
                           'needed': False,
                           'dest': 'sweep_type',
                           'default': SWEEP_LOG
                           },
                          {
                           'label': 'nsteps',
                           'pos': 1,
                           'type': float,
                           'needed': True,
                           'dest': 'points',
                           'default': None
                          },
                          {
                           'label': 'start',
                           'pos': 2,
                           'type': float,
                           'needed': True,
                           'dest': 'start',
                           'default': None
                          },
                          {
                           'label': 'stop',
                           'pos': 3,
                           'type': float,
                           'needed': True,
                           'dest': 'stop',
                           'default': None
                          })
               }
        }


def ac_analysis(circ, start, points, stop, sweep_type=None,
                x0=None, mna=None, AC=None, Nac=None, J=None,
                outfile="stdout"):

    # check step/start/stop parameters
    if start == 0:
        raise ValueError("ac_analysis(): AC analysis has start frequency = 0")
    if start > stop:
        raise ValueError("ac_analysis(): AC analysis has start > stop")
    if points < 2 and not start == stop:
        raise ValueError("ac_analysis(): AC analysis has number of points < 2 & start != stop")
    
    if sweep_type.upper() == SWEEP_LOG or sweep_type is None:
        fs = np.logspace(int(start), np.log(int(stop)), num=int(points), endpoint=True)
    elif sweep_type.upper() == SWEEP_LOG:
        fs = np.linspace(int(start), int(stop), num=int(points), endpoint=True)
    else:
        raise ValueError(f"ac_analysis(): unknown sweep type {sweep_type}")

    logging.info(f"Starting AC analysis")
    logging.info(f"Start Freq. : {start} Hz\tStop Freq. : {stop} Hz\n \
                 Using {points} points on a {sweep_type.lower()} axis")    
    
    # get the MNA matrices from the circuit object
    M0 = circ.M0
    ZAC0 = circ.ZAC0
    D0 = circ.D0
        
    # reduce the matrices
    M = M0[1:, 1:]
    ZAC = ZAC0[1:]
    D = D0[1:, 1:]
    
    if circ.is_nonlinear():
        logging.error("AC analysis does not currently support analysis of \
                      non-linear circuits")
        raise ValueError

    sol = results.Solution(circ, outfile, sol_type='AC', extra_header='f')
    

    j = np.complex('j')
    
    for f in fs:
        # evaluate the impedance at
        # the current frequency
        IMP = f * np.pi * 2 * j * D
        # solve using the complex solver
        x = complex_solve.solver((M + IMP), ZAC)
        # start row with frequency
        row = [f]
        # now append computations
        row.extend(x.transpose().tolist()[0])
        # write to file
        sol.write_data(row)
   
    sol.close()
    
    return sol.as_dict()
