#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian
"""

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

import numpy as np

#: Encoding of the netlist files.
encoding = 'utf8'

cache_len = 67108864 # 512MB

#: A boolean to differentiate command line execution from module import
#: When cli is False, no printing and no weird stdout stuff.
cli = False

# global: errors
#: Voltage absolute tolerance.
vea = 1e-6
#: Voltage relative tolerance.
ver = 1e-3
#: Current absolute tolerance.
iea = 1e-9
#: Current relative tolerance.
ier = 1e-3

# global: circuit
#: Minimum conductance to ground.
gmin = 1e-12
#: Should we show to the user results pertaining to nodes introduced by
#: components or by the simulator?
print_int_nodes = True

# global: solving
#: Dense matrix limit: if the dimensions of the square MNA matrix are bigger,
#: use sparse matrices.
# dense_matrix_limit = 400
#: Should we damp artificially the first NR iterations? See also
#: :func:`ahkab.dc_analysis.get_td`.
nr_damp_first_iters = False
#: In all NR iterations, lock the nodes controlling non-linear elements. See
#: also :func:`ahkab.dc_analysis.get_td`.
nl_voltages_lock = True     # Apply damping - slows down solution.
#: Non-linear nodes lock factor:
#: if we allow the voltage on controlling ports to change too much, we may
#: have current/voltage overflows. Think about the diode characteristic.
#: So we allow them to change of ``nl_voltages_lock_factor``
#: :math:`\cdot V_{th}` at most and damp all variables accordingly.
nl_voltages_lock_factor = 4

#: Whether the standard solving method can be used.
use_standard_solve_method = True
#: Whether the gmin-settping homothopy can be used.
use_gmin_stepping = True
#: Whether the source-stepping homothopy can be used.
use_source_stepping = True

#: When printing out to the user, whether we can suppress trailing zeros.
print_suppress = False
#: When printing out to the user, how many decimal digits to show at maximum.
print_precision = np.get_printoptions()['precision']

# dc
#: Maximum allowed NR iterations during a DC analysis.
dc_max_nr_iter = 10000
#: Enable guessing to init the NR solver during a DC analysis.
dc_use_guess = True
#: Do not perform an init DC guess if its effort is higher than
#: this value.
dc_max_guess_effort = 250000
# shorthand to set logarithmic stepping in DC analyses.
dc_log_step = 'LOG'
# shorthand to set linear stepping in DC analyses.
dc_lin_step = 'LIN'
#: Can we skip troublesome points during DC sweeps?
dc_sweep_skip_allowed = True

# transient
#: The default differentiation method for transient analyses.
default_tran_method = "TRAP"
#: Minimum allowed discretization step for time.
hmin = 1e-20
#: Maximum number of time iterations for transient analyses
#: Notice the default (0) means no limit is enforced.
transient_max_time_iter = 0  # disabled
#: Maximum number of NR iterations for transient analyses.
transient_max_nr_iter = 20
#: In a transisent analysis, if a prediction value is avalilable,
#: use it as first guess for ``x(n+1)``, otherwise ``x(n)`` is used.
transient_prediction_as_x0 = True
#: Use aposteriori step control?
transient_use_aposteriori_step_control = True
#: Step change threshold:
#: we do not want to redo the iteraction if the aposteriori check suggests a step
#: that is very close to the one we already used. A value of 0.9 seems to be a
#: good idea.
transient_aposteriori_step_threshold = 0.9
#: Disable all step control in transient analyses.
transient_no_step_control = False
#: Minimum capacitance to ground.
cmin = 1e-18


# ac
ac_log_step = 'LOG'
ac_lin_step = 'LIN'
#: Maximum number of NR iterations for AC analyses.
ac_max_nr_iter = 20
#: Use degrees instead of rads in AC phase results.
ac_phase_in_deg = False