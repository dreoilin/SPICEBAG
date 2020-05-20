# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

import sys
import re
import copy

# LU algorithms from /FORTRAN/
from .FORTRAN.LINALG import ludcmp, lubksb
from .FORTRAN.DC_SUBRS import gmin_mat
# vector norm
from numpy.linalg import norm

import numpy as np    

from . import components
from . import diode
from . import constants
from . import options
from . import circuit
from . import utilities
from . import results

# suuported homopothies
from .solvers import Standard, GminStepper, SourceStepper

from .utilities import convergence_check

import logging 
    
specs = {'op': {
    'tokens': ({
               'label': 'guess',
               'pos': None,
               'type': bool,
               'needed': False,
               'dest': 'guess',
               'default': options.dc_use_guess
               },
        {
               'label': 'ic_label',
               'pos': None,
               'type': str,
               'needed': False,
               'dest': 'x0',
               'default': None
               }
               )
},
    'dc': {'tokens': ({
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

def setup_solvers(Gmin=False):
    
    solvers = []
    if options.use_standard_solve_method:
        standard = Standard()
        solvers.append(standard)
    if options.use_gmin_stepping and Gmin:
        gmin_stepping = GminStepper()
        solvers.append(gmin_stepping)
    if options.use_source_stepping:
        source_stepping = SourceStepper()
        solvers.append(source_stepping)
    
    return solvers
    

def dc_solve(M, ZDC, circ, Ntran=None, Gmin=None, x0=None, time=None,
             MAXIT=options.dc_max_nr_iter, locked_nodes=None):
        
    M_size = M.shape[0]
    NNODES = circ.get_nodes_number()
    
    if locked_nodes is None:
        locked_nodes = circ.get_locked_nodes()
    
    if Gmin is None:
        Gmin = 0
        solvers = setup_solvers(Gmin=False)
    else:
        solvers = setup_solvers(Gmin=True)

    # call circuit method to generate AC component of input signal
    if time is not None:
        # get method would be nicer
        circ.generate_ZAC(time)
        # retrieve ZAC and add to DC component
        ZAC = circ.ZAC
    else:
        ZAC = False

    # if there is no initial guess, we start with 0
    if x0 is not None:
        if isinstance(x0, results.op_solution):
            x = x0.asarray()
        else:
            x = x0
    else:
        x = np.zeros((M_size, 1))

    convergence_by_node = None
    logging.info("Solving...")
    iters = 0
    
    converged = False
    
    for solver in solvers:
        logging.debug("Outer loop")
        logging.debug(solver.name)
        input()
        while (solver.failed is not True) and (not converged):
            logging.debug("Inside inner loop")
            logging.debug(solver.name)
            input()
            logging.debug("M and Z before augmentation")
            logging.debug(M)
            logging.debug(ZDC)
            # 1. Augment the matrices
            M, ZDC = solver.augment_M_and_ZDC(M, ZDC, Gmin)
            Z = ZDC + ZAC * (bool(time))
            logging.debug("After")
            logging.debug(M)
            logging.debug(Z)
            logging.debug("Has solver finished?")
            logging.debug(solver.finished)
            input()
            # 2. Try to solve with the current solver
            try:
                (x, error, converged, n_iter, convergence_by_node)\
                    = newton_solver(x, M, circ, Z=Z, nv=NNODES, 
                                    locked_nodes=locked_nodes,
                                    time=time, MAXIT=MAXIT)
            except ValueError:
                logging.warning("Singular matrix")
                converged = False
            except OverflowError:
                logging.warning("Overflow error detected...")
                converged = False
            # increment iteration
            iters += n_iter
            logging.debug("Did LU converge?")
            logging.debug(converged)
            logging.debug("Solution")
            logging.debug(x)
            input()
            if not converged:
                # check to find problem nodes
                if convergence_by_node is not None:
                    for ivalue in range(len(convergence_by_node)):
                        if not convergence_by_node[ivalue] and ivalue < NNODES - 1:
                            logging.debug("Convergence problem node %s" % (circ.int_node_to_ext(ivalue),))
                        elif not convergence_by_node[ivalue] and ivalue >= NNODES - 1:
                            e = circ.find_vde(ivalue)
                            print("Convergence problem current in %s" % e.part_id)
                # make sure iterations haven't been exceeded
                logging.debug("Number of iterations")
                logging.debug(iters)
                input()
                if n_iter == MAXIT - 1:
                    logging.error("Error: MAXIT exceeded (" + str(MAXIT) + ")")

                if solver.finished:
                    solver.fail()
                logging.debug("Has solver failed?")
                logging.debug(solver.failed)
                input()
            else:
                # check to see if stepping was completed...
                # if not, we go again using previous solution
                if not solver.finished:
                    converged = False
            logging.debug("I'm at the end of the loop")
            input()
    return (x, error, converged, iters)


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
                if isinstance(circ[index], components.sources.VSource):
                    source_elem = circ[index]
                    break
            if elem_type == 'i':
                if isinstance(circ[index], components.sources.ISource):
                    source_elem = circ[index]
                    break
    if not source_elem:
        raise ValueError(".DC: source %s was not found." % source)

    if isinstance(source_elem, components.sources.VSource):
        initial_value = source_elem.dc_value
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
        if isinstance(source_elem, components.sources.VSource):
            source_elem.dc_value = sweep_value
        else:
            source_elem.dc_value = sweep_value
        # silently calculate the op
        x = op_analysis(circ, x0=x, guess=guess, verbose=0)
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
    if isinstance(source_elem, components.sources.VSource):
        source_elem.dc_value = initial_value
    else:
        source_elem.dc_value = initial_value

    return sol if solved else None


def op_analysis(circ, x0=None, guess=True, outfile=None, verbose=3):
    
    if not options.dc_use_guess:
        guess = False
    
    logging.debug("Getting M0 and ZDC0 from circuit")
    # unreduced MNA matrices computed by the circuit object
    M0 = circ.M0
    ZDC0 = circ.ZDC0
    # now create reduced matrices (used for calculation purposes)
    logging.debug("Reducing MNA matrices")
    M = M0[1:, 1:]
    ZDC = ZDC0[1:]
    
    logging.info("Starting operating point analysis")
    
    # Assign DC estimate here

    ##########################################################################
    # Attempt to solve with Gmin
    ##########################################################################
    logging.info("Constructing Gmin matrix")
    # take away a single node because we have reduced M
    Gmin_matrix = gmin_mat(options.gmin, M.shape[0], circ.get_nodes_number()-1)
    (x_min, e_min, converged, iters_min) = dc_solve(M, ZDC,
                                              circ, Gmin=Gmin_matrix, x0=x0)
    ##########################################################################
    
    if converged:
        # Create an op solution object
        op_min = results.op_solution(
            x_min, e_min, circ, outfile=outfile, iterations=iters_min)
        # now try without Gmin
        logging.info("Now attempting without Gmin:")
        (x, e, solved, iters) = dc_solve(
            M, ZDC, circ, Gmin=None, x0=x_min)
    else:
        solved = False

    if converged and not solved:
        logging.error("Can't solve without Gmin.")
        
        logging.info("Displaying latest valid results.")
        op_min.write_to_file(filename='stdout')
        opsolution = op_min
    elif converged and solved:
        op = results.op_solution(
            x, e, circ, outfile=outfile, iterations=iters_min + iters)
        op.gmin = 0
        opsolution = op
    else:
        logging.error("Couldn't solve the circuit. Giving up.")
        opsolution = None

    if opsolution and outfile != 'stdout' and outfile is not None:
        opsolution.write_to_file()

    return opsolution


def newton_solver(x, M, circ, Z, MAXIT, nv, locked_nodes, time=None, vector_norm=lambda v: max(abs(v))):

    """
    
    """    

    M_size = M.shape[0]
    N = np.zeros((M_size, 1))
    J = np.zeros((M_size, M_size))
    nl = circ.is_nonlinear()
    
    if x is None:
        x = np.zeros((M_size, 1))
    else:
        if x.shape[0] != M_size:
            raise ValueError("x0s size is different from expected: got "
                             "%d-elements x0 with an MNA of size %d" %
                             (x.shape[0], M_size))
    if Z is None:
        logging.warning(
            "No sources in circuit? Z is None")
        Z = np.zeros((M_size, 1))

    converged = False
    iters = 0
    
    while iters < MAXIT:
        # build the Nonlinear and Jacobian matrices
        if nl:
            N[:, 0] = 0.0
            for elem in circ:
                if elem.is_nonlinear:
                    _update_J_and_Tx(J, N, x, elem, time)
        # dot product is an intrinsic fortran routine
        residual = M.dot(x) + Z + nl*N
        
        ##########################################################
        # Solve linear system of equations
        ##########################################################
        LU, INDX, _, C = ludcmp(M + nl*J, M_size)
        if C == 1:
            raise ValueError
        
        dx = lubksb(LU, INDX,  -residual)
        # check for overflow error
        if norm(dx) == np.nan:
            raise OverflowError
        ##########################################################
        # we've done the hard work, now iterate
        iters += 1
        # perform newton update
        x = x + get_td(dx, locked_nodes, n=iters) * dx
        
        # if the circuit is linear, we know it has converged upon solution after one iteration
        if not nl:
            converged = True
            convergence_by_node = []
            break
        # otherwise we need to check it
        else:
            # run the convergence check
            converged, convergence_by_node = convergence_check(
            x, dx, residual, nv - 1, debug=True)
            if converged:
                convergence_by_node = []
            break

    return (x, residual, converged, iters, convergence_by_node)


def _update_J_and_Tx(J, Tx, x, elem, time):
    out_ports = elem.get_output_ports()
    for index in range(len(out_ports)):
        n1, n2 = out_ports[index]
        n1m1, n2m1 = n1 - 1, n2 - 1
        dports = elem.get_drive_ports(index)
        v_dports = []
        for port in dports:
            v = 0.  # build v: remember we removed the 0 row and 0 col of mna -> -1
            if port[0]:
                v = v + x[port[0] - 1, 0]
            if port[1]:
                v = v - x[port[1] - 1, 0]
            v_dports.append(v)
        if hasattr(elem, 'gstamp') and hasattr(elem, 'istamp'):
            iis, gs = elem.gstamp(v_dports, time)
            J[iis] += gs.reshape(-1)
            iis, i = elem.istamp(v_dports, time)
            Tx[iis] += i.reshape(-1)
            continue
        if n1 or n2:
            iel = elem.i(index, v_dports, time)
        if n1:
            Tx[n1m1, 0] = Tx[n1m1, 0] + iel
        if n2:
            Tx[n2m1, 0] = Tx[n2m1, 0] - iel
        for iindex in range(len(dports)):
            if n1 or n2:
                g = elem.g(index, v_dports, iindex, time)
            if n1:
                if dports[iindex][0]:
                    J[n1m1, dports[iindex][0] - 1] += g
                if dports[iindex][1]:
                    J[n1m1, dports[iindex][1] - 1] -= g
            if n2:
                if dports[iindex][0]:
                    J[n2m1, dports[iindex][0] - 1] -= g
                if dports[iindex][1]:
                    J[n2m1, dports[iindex][1] - 1] += g


def get_td(dx, locked_nodes, n=-1):
    

    if not options.nr_damp_first_iters or n < 0:
        td = 1
    else:
        if n < 10:
            td = 1e-2
        elif n < 20:
            td = 0.1
        else:
            td = 1
    td_new = 1
    if options.nl_voltages_lock:
        for (n1, n2) in locked_nodes:
            if n1 != 0:
                if n2 != 0:
                    if abs(dx[n1 - 1, 0] - dx[n2 - 1, 0]) > options.nl_voltages_lock_factor * constants.Vth():
                        td_new = (options.nl_voltages_lock_factor * constants.Vth()) / abs(
                            dx[n1 - 1, 0] - dx[n2 - 1, 0])
                else:
                    if abs(dx[n1 - 1, 0]) > options.nl_voltages_lock_factor * constants.Vth():
                        td_new = (options.nl_voltages_lock_factor * constants.Vth()) / abs(
                            dx[n1 - 1, 0])
            else:
                if abs(dx[n2 - 1, 0]) > options.nl_voltages_lock_factor * constants.Vth():
                    td_new = (options.nl_voltages_lock_factor * constants.Vth()) / abs(
                        dx[n2 - 1, 0])
            if td_new < td:
                td = td_new
    return td


def build_x0_from_user_supplied_ic(circ, icdict):
    
    Vregex = re.compile("V\s*\(\s*([a-z0-9]+)\s*\)", re.IGNORECASE | re.DOTALL)
    Iregex = re.compile("I\s*\(\s*([a-z0-9]+)\s*\)", re.IGNORECASE | re.DOTALL)
    nv = circ.get_nodes_number()  # number of voltage variables
    voltage_defined_elem_names = \
        [elem.part_id.lower() for elem in circ
         if circuit.is_elem_voltage_defined(elem)]
    ni = len(voltage_defined_elem_names)  # number of current variables
    x0 = np.zeros((nv + ni, 1))
    for label in icdict.keys():
        value = icdict[label]
        if Vregex.search(label):
            ext_node = Vregex.findall(label)[0]
            int_node = circ.ext_node_to_int(ext_node)
            x0[int_node, 0] = value
        elif Iregex.search(label):
            element_name = Iregex.findall(label)[0]
            index = voltage_defined_elem_names.index(element_name.lower())
            x0[nv + index, 0] = value
        else:
            raise ValueError("Unrecognized label " + label)
    return x0[1:, :]


def modify_x0_for_ic(circ, x0):
    

    if isinstance(x0, results.op_solution):
        x0 = copy.copy(x0.asarray())
        return_obj = True
    else:
        return_obj = False

    nv = circ.get_nodes_number()  # number of voltage variables
    voltage_defined_elements = [
        x for x in circ if circuit.is_elem_voltage_defined(x)]

    # setup voltages this may _not_ work properly
    for elem in circ:
        if isinstance(elem, components.Capacitor) and elem.ic or \
                isinstance(elem, diode.diode) and elem.ic:
            x0[elem.n1 - 1, 0] = x0[elem.n2 - 1, 0] + elem.ic

    # setup the currents
    for elem in voltage_defined_elements:
        if isinstance(elem, components.Inductor) and elem.ic:
            x0[nv - 1 + voltage_defined_elements.index(elem), 0] = elem.ic

    if return_obj:
        xnew = results.op_solution(x=x0, \
            error=np.zeros(x0.shape), circ=circ, outfile=None)
        xnew.netlist_file = None
        xnew.netlist_title = "Self-generated OP to be used as tran IC"
    else:
        xnew = x0

    return xnew


