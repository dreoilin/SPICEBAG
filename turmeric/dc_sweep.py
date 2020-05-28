#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 25 18:07:33 2020

@author: cian
"""
import logging
import numpy as np

# linear components
from . import components
from . import settings
from . import results
from . import dc

specs = {'dc': {'tokens': ({
                      'label': 'source',
                      'pos': 0,
                      'type': str,
                      'needed': True,
                      'dest': 'source',
                      'default': None
                      },
                      {
                      'label': 'start',
                      'pos': 1,
                      'type': float,
                      'needed': True,
                      'dest': 'start',
                      'default': None
                      },
                      {
                      'label': 'stop',
                      'pos': 2,
                      'type': float,
                      'needed': True,
                      'dest': 'stop',
                      'default': None
                      },
                      {
                      'label': 'step',
                      'pos': 3,
                      'type': float,
                      'needed': True,
                      'dest': 'step',
                      'default': None
                      },
                      {
                      'label': 'type',
                      'pos': None,
                      'type': str,
                      'needed': False,
                      'dest': 'sweep_type',
                      'default': 'LIN'
                      }
                     )
           }
    }

def dc_analysis(circ, start, stop, step, source, sweep_type='LINEAR', guess=True, x0=None, outfile="stdout"):
    
    logging.info("Starting DC sweep...")
    source_label = source.upper()
    
    points = int((stop - start) / step)
    sweep_type = sweep_type.upper()[:3]
    
    if sweep_type == 'LOG' and stop - start < 0:
        logging.error("dc_analysis(): DC analysis has log sweeping and negative stepping.")
        raise ValueError
    if (stop - start) * step < 0:
        logging.error("Unbounded stepping in DC analysis.")
        raise ValueError
    
    if sweep_type == 'LOG':
        dcs = np.logspace(int(start), np.log(int(stop)), num=int(points), endpoint=True)
    elif sweep_type == 'LIN' or sweep_type is None:
        dcs = np.linspace(int(start), int(stop), num=int(points), endpoint=True)

    if source_label[0] != ('V' or 'I'):
        logging.error("Sweeping is possible only with voltage and current sources.")
        raise ValueError(f"Source is type: {source_label[0]}")
      
    source = None
    for elem in [src for src in circ if isinstance(src, (components.sources.V, components.sources.I))]:
        identifier = f"{elem.name.upper()}{elem.part_id}"
        if identifier == source_label:
            source = elem
            logging.debug("dc_analysis(): Source found!")
            break
        logging.error("dc_analysis(): Specified source was not found")
        raise ValueError("dc_analysis(): source {source} was not found")
    
    # store this value to reassign later
    val_ = source.dc_value
     
    M_size = circ.M0.shape[0] - 1
    x = format_estimate(x0, M_size)
    logging.info("dc_analysis(): DC analysis starting...")
    sol = results.Solution(circ, None, 'DC', extra_header=source_label)
    # sweep setup
    solved = False
    for i, sweep_value in enumerate(dcs):
        source.dc_value = sweep_value
        # regenerate the matrices with new sweep value
        _ = circ.gen_matrices()
        # now call an operating point analysis
        x = dc.op_analysis(circ, x0=x, guess=guess, verbose=0)
        if x is None:
            logging.warning("dc_analysis(): Coudn't compute \
                            operating point for {sweep_value}. \
                                Skipping...")
            # skip
            continue
        x = np.array([float(value[0]) for value in x.values()])
        
        
        row = [sweep_value]
        row.extend(x)
        sol.write_data(row)
        # only flag as solved if loop doesn't skip any values
        solved = True

        
    
    logging.info("dc_analysis(): Finished DC analysis")
    if not solved:
        logging.error("dc_analysis(): Couldn't solve for values in DC sweep")
        return None
    
    # ensure that DC source retains initial value
    source.dc_value = val_
    
    return sol.as_dict()


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
