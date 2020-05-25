#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from . import options
from . import results
import logging

specs = {'ac': {'tokens': ({
                           'label': 'type',
                           'pos': 0,
                           'type': str,
                           'needed': False,
                           'dest': 'sweep_type',
                           'default': options.ac_log_step
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
    
    if sweep_type.upper() == options.ac_log_step or sweep_type is None:
        fs = np.logspace(int(start), np.log(int(stop)), num=int(points), endpoint=True)
    elif sweep_type.upper() == options.ac_lin_step:
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
    #mats = [M0, ZAC0, D0]
    #keys = ['M0', 'ZAC0', 'D0']
    #for mat in zip(keys, mats):
    #    print(mat)
    #    
    #input()
        
    # reduce the matrices
    M = M0[1:, 1:]
    ZAC = ZAC0[1:]
    D = D0[1:, 1:]
    ZAC[0,0] = 1
    if circ.is_nonlinear():
        logging.error("AC analysis does not currently support analysis of \
                      non-linear circuits")
        raise ValueError

    sol = results.ac_solution(circ, start=start, stop=stop, points=points,
                              stype=sweep_type, op=x0, outfile=outfile)

    j = np.complex('j')
    print(fs)
    for f in fs:
        # evaluate the impedance at
        # the current frequency
        IMP = f * np.pi * 2 * j * D
        try:
            x = np.linalg.solve((M + IMP), ZAC)
        except OverflowError:
            logging.error(f"ac_analysis(): Numpy couldn't solve the \
                          system at {f} Hz due to an overflow error")
            raise ValueError
        except np.linalg.LinAlgError as e:
            if 'Singular matrix' in str(e):
                logging.error(f"ac_analysis(): singular matrix detected \
                              at {f} Hz")
                raise ValueError
        sol.add_line(f, x)
   
    return sol