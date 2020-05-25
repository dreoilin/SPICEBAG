#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 25 18:07:33 2020

@author: cian
"""
import sys
import logging


# linear components
from . import components
from . import options
from . import utilities
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
                      'default': options.dc_lin_step
                      }
                     )
           }
    }

def dc_analysis(circ, start, stop, step, source, sweep_type='LINEAR', guess=True, x0=None, outfile="stdout"):
    
    logging.info("Starting DC analysis:")
    elem_type, elem_descr = source[0].lower(), source.lower()
    sweep_label = elem_type[0].upper() + elem_descr[1:]

    if sweep_type == options.dc_log_step and stop - start < 0:
        logging.error("DC analysis has log sweeping and negative stepping.")
        sys.exit(1)
    if (stop - start) * step < 0:
        raise ValueError("Unbounded stepping in DC analysis.")

    points = (stop - start) / step + 1
    sweep_type = sweep_type.upper()[:3]

    if sweep_type == options.dc_log_step:
        dc_iter = utilities.log_axis_iterator(start, stop, points=points)
    elif sweep_type == options.dc_lin_step:
        dc_iter = utilities.lin_axis_iterator(start, stop, points=points)
    else:
        logging.error("Unknown sweep type: %s" % (sweep_type,))
        sys.exit(1)

    if elem_type != 'v' and elem_type != 'i':
        logging.error("Sweeping is possible only with voltage and current sources. (" + str(elem_type) + ")")
        sys.exit(1)

    source_elem = None
    for index in range(len(circ)):
        if circ[index].part_id.lower() == elem_descr:
            if elem_type == 'v':
                if isinstance(circ[index], components.sources.V):
                    source_elem = circ[index]
                    break
            if elem_type == 'i':
                if isinstance(circ[index], components.sources.ISource):
                    source_elem = circ[index]
                    break
    if not source_elem:
        raise ValueError(".DC: source %s was not found." % source)

    if isinstance(source_elem, components.sources.V):
        initial_value = source_elem.value
    else:
        initial_value = source_elem.dc_value

    x = x0

    sol = results.dc_solution(
        circ, start, stop, sweepvar=sweep_label, stype=sweep_type, outfile=outfile)

    logging.info("Solving... ")

    # sweep setup
    
    index = 0
    for sweep_value in dc_iter:
        index = index + 1
        if isinstance(source_elem, components.sources.V):
            source_elem.value = sweep_value
        else:
            source_elem.dc_value = sweep_value
        # silently calculate the op
        x = dc.op_analysis(circ, x0=x, guess=guess, verbose=0)
        if x is None:
            if not options.dc_sweep_skip_allowed:
                logging.info("Could't solve the circuit for sweep value:", start + index * step)
                solved = False
                break
            else:
                logging.info("Skipping sweep value:", start + index * step)
                continue
        solved = True
        sol.add_op(sweep_value, x)

        
    if solved:
        logging.info("done")

    # clean up
    if isinstance(source_elem, components.sources.V):
        source_elem.value = initial_value
    else:
        source_elem.dc_value = initial_value

    return sol if solved else None