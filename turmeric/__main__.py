#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian
"""

import sys
import logging
from optparse import OptionParser

from . import turmeric
from . import options
from . import transient
from . import utilities
from .__version__ import __version__

def _cli():
    usage = f"usage: \t%prog [options] <filename>\n\n"\
            f"filename - netlist of circuit to simulate.\n\n"\
            f"Welcome to Turmeric, version {__version__}\n"
    parser = OptionParser(usage, version="%prog " + __version__)

    # general options
    parser.add_option("-v", "--verbose", action="store_true",
            dest="verbose", default=False, help="Verbose output [Not implemented]")
    # TODO: Implement outputting of parsed circuit
    #parser.add_option("-p", "--print", action="store_true",
    #                  dest="print_circuit", default=False, help="Output parsed circuit")
    parser.add_option("-o", "--outfile", action="store", type="string",
                      dest="outfile", default='stdout', help="Prefix to use for generated files. Defaults to stdout.")
    #parser.add_option("", "--dc-guess", action="store", type="string",
    #                  dest="dc_guess", default="guess", help="Guess to be " +
    #                  "used to start a OP or DC analysis: none or guess. " +
    #                  "Defaults to guess.")
    #parser.add_option("-t", "--tran-method", action="store", type="string",
    #                  dest="method", default=transient.TRAP.lower(),
    #                  help="Method to be used in transient analysis: " +
    #                  transient.IMPLICIT_EULER.lower() + ", " +
    #                  transient.TRAP.lower() + ", " +
    #                  transient.GEAR2.lower() + ", " +
    #                  transient.GEAR3.lower() + ", " +
    #                  transient.GEAR4.lower() + ", " +
    #                  transient.GEAR5.lower() + " or " +
    #                  transient.GEAR6.lower() + ". Defaults to TRAP.")
    #parser.add_option("", "--t-fixed-step", action="store_true",
    #                  dest="no_step_control", default=False, help="Disables" +
    #                  " the step control in transient analysis.")
    #parser.add_option("", "--v-absolute-tolerance", action="store",
    #                  type="string", dest="vea", default=None, help="Voltage" +
    #                  " absolute tolerance. Default: " + str(options.vea) + " V")
    #parser.add_option("", "--v-relative-tolerance", action="store",
    #                  type="string", dest="ver", default=None, help="Voltage " +
    #                  "relative tolerance. Default: " + str(options.ver))
    #parser.add_option("", "--i-absolute-tolerance", action="store",
    #                  type="string", dest="iea", default=None, help="Current " +
    #                  "absolute tolerance. Default: " + str(options.iea) + " A")
    #parser.add_option("", "--i-relative-tolerance", action="store",
    #                  type="string", dest="ier", default=None, help="Current " +
    #                  "relative tolerance. Default: " + str(options.ier))
    #parser.add_option("", "--h-min", action="store", type="string",
    #                  dest="hmin", default=None, help="Minimum time step. " +
    #                  "Default: " + str(options.hmin))
    #parser.add_option("", "--dc-max-nr", action="store", type="string",
    #                  dest="dc_max_nr_iter", default=None, help="Maximum " +
    #                  "number of NR iterations for DC and OP analyses. " +
    #                  "Default: " + str(options.dc_max_nr_iter))
    #parser.add_option("", "--t-max-nr", action="store", type="string",
    #                  dest="transient_max_nr_iter", default=None,
    #                  help="Maximum number of NR iterations for each time " +
    #                  "step during transient analysis. Default: " +
    #                  str(options.transient_max_nr_iter))
    #parser.add_option("", "--t-max-time", action="store", type="string",
    #                  dest="transient_max_time_iter", default=None,
    #                  help="Maximum number of time iterations during " +
    #                  "transient analysis. Setting it to 0 (zero) disables " +
    #                  "the limit. Default: " +
    #                  str(options.transient_max_time_iter))
    #parser.add_option("", "--gmin", action="store", type="string", dest="gmin",
    #                  default=None, help="The minimum conductance to ground. " +
    #                  "Inserted when requested. Default: " +
    #                  str(options.gmin))
    #parser.add_option("", "--cmin", action="store", type="string", dest="cmin",
    #                  default=None, help="The minimum capacitance to ground. " +
    #                  "Default: " + str(options.cmin))

    (cli_options, remaning_args) = parser.parse_args()

    verbose = int(cli_options.verbose)
    #if cli_options.method is not None:
    #    options.default_tran_method = cli_options.method.upper()
    #if cli_options.vea is not None:
    #    options.vea = float(cli_options.vea)
    #if cli_options.ver is not None:
    #    options.ver = float(cli_options.ver)
    #if cli_options.iea is not None:
    #    options.iea = float(cli_options.iea)
    #if cli_options.ier is not None:
    #    options.ier = float(cli_options.ier)
    #if cli_options.hmin is not None:
    #    options.hmin = float(cli_options.hmin)
    #if cli_options.dc_max_nr_iter is not None:
    #    options.dc_max_nr_iter = int(float(cli_options.dc_max_nr_iter))
    #if cli_options.transient_max_nr_iter is not None:
    #    options.transient_max_nr_iter = int(
    #        float(cli_options.transient_max_nr_iter))
    #if cli_options.transient_max_time_iter is not None:
    #    options.transient_max_time_iter = int(
    #        float(cli_options.transient_max_time_iter))
    #if cli_options.gmin is not None:
    #    options.gmin = float(cli_options.gmin)
    #if cli_options.cmin is not None:
    #    options.cmin = float(cli_options.cmin)

    if not len(remaning_args) == 1:
        print("Usage: python -m turmeric [options] <filename>\npython -m turmeric -h for help")
        sys.exit(1)
    #if remaning_args[0] == '-':
    #    read_netlist_from_stdin = True
    #else:
    #    read_netlist_from_stdin = False
    #if not read_netlist_from_stdin and not utilities.check_file(remaning_args[0]):
    #    sys.exit(23)

    #options.transient_no_step_control = cli_options.no_step_control
    #options.dc_use_guess = cli_options.dc_guess
    #options.cli = True
    #turmeric._print = cli_options.print_circuit

    # Set up logging
    #logging.basicConfig(format='%(asctime)|%(levelname)|%(message)s', filename='turmeric.log', filemode='w', level=logging.DEBUG)
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s : %(threadName)s : %(name)s : %(levelname)s : %(message)s')
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    if (verbose):
        sh.setLevel(logging.INFO)
    else:
        sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)

    lfh = logging.FileHandler(f'{cli_options.outfile}.log',mode='w',encoding='utf8')
    lfh.setLevel(logging.DEBUG)
    lfh.setFormatter(formatter)
    logger.addHandler(lfh)
    logger.addHandler(sh)

    #logging.config.fileConfig("logging.conf")
    
    # Program execution
    # TODO: implement verbosity by passing verbose=verbose
    turmeric.main(filename=remaning_args[0], outfile=cli_options.outfile)

    sys.exit(0)

if __name__ == "__main__":
    _cli()
