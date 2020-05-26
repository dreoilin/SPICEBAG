# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

import sys
import logging

from .FORTRAN.LU import ludcmp, lubksb
from .FORTRAN.DC_SUBRS import gmin_mat
from .FORTRAN.DET import determinant

from numpy.linalg import norm
import numpy as np    

# linear components
from .components import VoltageDefinedComponent
from . import constants
from . import options
from . import utilities
from . import results
from . import solvers as slv

from .utilities import convergence_check
    
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
    }
}
    

def dc_solve(M, ZDC, circ, Gmin=None, x0=None, time=None,
             MAXIT=options.dc_max_nr_iter, locked_nodes=None):
        
    M_size = M.shape[0]
    NNODES = circ.get_nodes_number()
    
    if locked_nodes is None:
        locked_nodes = circ.get_locked_nodes()
    
    if Gmin is None:
        Gmin = 0
        solvers = slv.setup_solvers(Gmin=False)
    else:
        solvers = slv.setup_solvers(Gmin=True)

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

    logging.info("Solving...")
    iters = 0
    
    converged = False
    
    for solver in solvers:
        while (solver.failed is not True) and (not converged):
            logging.info(f"Now solving with: {solver.name}")
            # 1. Augment the matrices
            M_, ZDC_ = solver.operate_on_M_and_ZDC(np.array(M),\
                                    np.array(ZDC), np.array(Gmin))
            Z = ZDC_ + ZAC * (bool(time))
            # 2. Try to solve with the current solver
            try:
                (x, error, converged, n_iter)\
                    = newton_solver(x, M_, circ, Z=Z, nv=NNODES, 
                                    locked_nodes=locked_nodes,
                                    time=time, MAXIT=MAXIT)
                # increment iteration
                iters += n_iter
            except ValueError:
                logging.critical("Singular matrix")
                converged = False
                error = None
                x = None
                solver.fail()
            
            except OverflowError:
                logging.critical("Overflow error detected...")
                converged = False
                error = None
                x = None
                solver.fail()
            
            if not converged:
                
                # make sure iterations haven't been exceeded
                if iters == MAXIT - 1:
                    logging.error("Error: MAXIT exceeded (" + str(MAXIT) + ")")

                if solver.finished:
                    solver.fail()
            else:
                # check to see if stepping was completed...
                # if not, we go again using previous solution
                if not solver.finished:
                    converged = False
                    
    return (x, error, converged, iters)


def op_analysis(circ, x0=None, guess=True, outfile=None, verbose=3):
    
    """
    This function is the entry point for an operating point analysis
    The analysis sets up the MNA matrices using a circuit object and constructs
    the Gmin matrix used in the dc solve homopothies
    
    A circuit solution is attempted twice:
        - Once with a Gmin matrix and
        - a second time without (to enhance results)
        
    If the analysis cannot find a solution without Gmin, the Gmin solution is
    returned with a warning. In this case, a solution is heavily dependent on
    the minimum conductance to ground.
    
    If the circuit cannot be solved using any of the available solving methods,
    the special value None is returned
    """
    
    logging.debug("op_analysis(): getting M0 and ZDC0 from circuit")
    # unreduced MNA matrices computed by the circuit object
    M0 = circ.M0
    ZDC0 = circ.ZDC0
    # now create reduce matrices (used for calculation purposes)
    logging.debug("op_analysis(): Reducing M0 and ZDC0 matrices")
    M = M0[1:, 1:]
    ZDC = ZDC0[1:]
    
    logging.info("Beginning operating point analysis")
    
    ##########################################################################
    # Set up auxiliary solving assistance
    ##########################################################################
    
    ### This calls a function to analyse the circuit topology and try to 
    # compute an educational guess as to where the values will converge
    # A guess is only needed if
    # 1. We don't already have one
    # 2. Circuit contains non-linear elements
    # 3. User has specified to use DC guess
    if x0 is None and guess and circ.is_nonlinear():
        logging.debug("op_analysis(): creating a (rough) estimate")
        x0 = dc_estimator(circ)

    logging.debug("op_analysis(): constructing Gmin matrix")
    # take away a single node because we have reduced M
    Gmin_matrix = gmin_mat(options.gmin, M.shape[0], circ.get_nodes_number()-1)
    ##########################################################################
    
    logging.info("op_analysis(): solving with Gmin")
    # now solve
    (x_min, e_min, converged, iters_min) = dc_solve(M, ZDC,
                                              circ, Gmin=Gmin_matrix, x0=x0)
    
    # convergence specifies a solution, but using Gmin
    if converged:
        # Create an op solution object
        op_min = results.op_solution(
            x_min, e_min, circ, outfile=outfile, iterations=iters_min)
        # now try without Gmin
        logging.info("op_analysis(): now attempting without Gmin:")
        (x, e, solved, iters) = dc_solve(
            M, ZDC, circ, Gmin=None, x0=x_min)
    else:
        solved = False
    
    # solution specifies solving without Gmin
    if converged and not solved:
        logging.error("Can't solve without Gmin.")
        logging.warning("Solution is highly dependent on Gmin")
        logging.info("Displaying latest valid results.")
        op_min.write_to_file(filename='stdout')
        opsolution = op_min
    elif converged and solved:
        # this is ideal - we have solved without Gmin
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
            J[:, :] = 0.0
            N[:, 0] = 0.0
            for elem in circ:
                if elem.is_nonlinear:
                    _update_J_and_N(J, N, x, elem, time)
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
            # convergence_by_node = []
            break
        # otherwise we need to check it
        else:
            # run the convergence check
            converged, _= convergence_check(
            x, dx, residual, nv - 1, debug=True)
            if converged:
                # convergence_by_node = []
                break

    return (x, residual, converged, iters)


def _update_J_and_N(J, Tx, x, elem, time):
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


def dc_estimator(circ):

    nv = circ.get_nodes_number()
    M = np.zeros((1, nv))
    T = np.zeros((1, 1))
    index = 0
    v_eq = 0  # number of current equations
    one_element_with_dc_guess_found = False

    for elem in circ:
        # In the meanwhile, check how many current equations are
        # required to solve the circuit
        if isinstance(elem, VoltageDefinedComponent):
            v_eq = v_eq + 1
        # This is the main focus: build a system of equations (M*x = T)
        if hasattr(elem, "dc_guess") and elem.dc_guess is not None:
            if not one_element_with_dc_guess_found:
                one_element_with_dc_guess_found = True
            if elem.is_nonlinear:
                port_index = 0
                for (n1, n2) in elem.ports:
                    if n1 == n2:
                        continue
                    if index:
                        M = utilities.expand_matrix(M, add_a_row=True,
                                                    add_a_col=False)
                        T = utilities.expand_matrix(T, add_a_row=True,
                                                    add_a_col=False)
                    M[index, n1] = +1
                    M[index, n2] = -1
                    T[index] = elem.dc_guess[port_index]
                    port_index = port_index + 1
                    index = index + 1
            else:
                if elem.n1 == elem.n2:
                    continue
                if index:
                    M = utilities.expand_matrix(M, add_a_row=True,
                                                add_a_col=False)
                    T = utilities.expand_matrix(T, add_a_row=True,
                                                add_a_col=False)
                M[index, elem.n1] = +1
                M[index, elem.n2] = -1
                T[index] = elem.dc_guess[0]
                index = index + 1

    M = utilities.remove_row_and_col(M, rrow=10 * M.shape[0], rcol=0)

    if not one_element_with_dc_guess_found:
        #if verbose == 5:
        #    print("DBG: get_dc_guess(): no element has a dc_guess")
       # elif verbose <= 3:
        #    print("skipped.")
        #return None
        pass

    # We wish to find the linearly dependent lines of the M matrix.
    # The matrix is made by +1, -1, 0 elements.
    # Hence, if two lines are linearly dependent, one of these equations
    # has to be satisfied: (L1, L2 are two lines)
    # L1 + L2 = 0 (vector)
    # L2 - L1 = 0 (vector)
    # This is tricky, because I wish to remove lines of the matrix while
    # browsing it.
    # We browse the matrix by line from bottom up and compare each line
    # with the upper lines. If a linearly dep. line is found, we remove
    # the current line.
    # Then break from the loop, get the next line (bottom up), which is
    # the same we were considering before; compare with the upper lines..
    # Not optimal, but it works.
    for i in range(M.shape[0] - 1, -1, -1):
        for j in range(i - 1, -1, -1):
            # print i, j, M[i, :], M[j, :]
            dummy1 = M[i, :] - M[j, :]
            dummy2 = M[i, :] + M[j, :]
            if not dummy1.any() or not dummy2.any():
                # print "REM:", M[i, :]
                M = utilities.remove_row(M, rrow=i)
                T = utilities.remove_row(T, rrow=i)
                break

    # Remove empty columns:
    # If a column is empty, we have no guess regarding the corresponding
    # node. It makes the matrix singular. -> Remove the col & remember
    # that we are _not_ calculating a guess for it.
    removed_index = []
    for i in range(M.shape[1] - 1, -1, -1):
        if not M[:, i].any():
            M = utilities.remove_row_and_col(M, rrow=M.shape[0], rcol=i)
            removed_index.append(i)

    # Now, we have a set of equations to be solved.
    # There are three cases:
    # 1. The M matrix has a different number of rows and columns.
    #    We use the Moore-Penrose matrix inverse to get
    #    the shortest length least squares solution to the problem
    #          M*x + T = 0
    # 2. The matrix is square.
    #    It seems that if the circuit is not pathological,
    #    we are likely to find a solution (the matrix has det != 0).
    #    I'm not sure about this though.

    if M.shape[0] != M.shape[1]:
        Rp = np.dot(np.linalg.pinv(M), T)
    else:  # case M.shape[0] == M.shape[1], use normal
        if np.linalg.det(M) != 0:
            try:
                Rp = np.dot(np.linalg.inv(M), T)
            except np.linalg.linalg.LinAlgError:
                eig = np.linalg.eig(M)[0]
                cond = abs(eig).max() / abs(eig).min()
                
                return None
        else:
            
            return None

    # Now we want to:
    # 1. Add voltages for the nodes for which we have no clue to guess.
    # 2. Append to each vector of guesses the values for currents in
    #    voltage defined elem.
    # Both them are set to 0
    for index in removed_index:
        Rp = np.concatenate((np.concatenate((Rp[:index, 0].reshape((-1, 1)),
                                             np.zeros((1, 1))), axis=0),
                             Rp[index:, 0].reshape((-1, 1))), axis=0)
    # add the 0s for the currents due to the voltage defined
    # elements (we have no guess for those...)
    if v_eq > 0:
        Rp = np.concatenate((Rp, np.zeros((v_eq, 1))), axis=0)


    return Rp
