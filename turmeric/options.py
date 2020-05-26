#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian
"""

import numpy as np

#: Encoding of the netlist files.
encoding = 'utf8'

cache_len = 67108864

cli = False

############################
#      Tolerances          #
############################
#: Voltage absolute tolerance.
vea = 1e-6
#: Voltage relative tolerance.
ver = 1e-3
#: Current absolute tolerance.
iea = 1e-9
#: Current relative tolerance.
ier = 1e-3
#: Minimum conductance to ground.
gmin = 1e-12
#: Should we show to the user results pertaining to nodes introduced by
#: components or by the simulator?
print_int_nodes = True

############################
#      Newton Method       #
############################
nr_damp_first_iters = False
nl_voltages_lock = True
nl_voltages_lock_factor = 4

############################
#      Homopothies         #
############################
use_standard_solve_method = True
use_gmin_stepping = True
use_source_stepping = True

#: When printing out to the user, how many decimal digits to show at maximum.
print_precision = np.get_printoptions()['precision']

############################
#      DC Analysis         #
############################
dc_max_nr_iter = 1000
dc_use_guess = True
dc_max_guess_effort = 250000
dc_sweep_skip_allowed = True

############################
#       Transient          #
############################

default_tran_method = "TRAP"
hmin = 1e-20
transient_max_nr_iter = 20
transient_prediction_as_x0 = True


# ac
ac_log_step = 'LOG'
ac_lin_step = 'LIN'
#: Maximum number of NR iterations for AC analyses.
ac_max_nr_iter = 20
#: Use degrees instead of rads in AC phase results.
ac_phase_in_deg = False