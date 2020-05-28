"""
Configuration options for turmeric

These values can be overwritten by those in a config.json file in the root directory and that is the preferred place to specify options
"""
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

############################
#      DC Analysis         #
############################
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
