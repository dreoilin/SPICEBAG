# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

import logging

from .FORTRAN.LU import ludcmp, lubksb
from .FORTRAN.DC_SUBRS import gmin_mat

from numpy.linalg import norm
import numpy as np    

from . import units
from . import settings
from . import solvers as slv
from . import results

specs = {'op': {'tokens' : {} }}
    

def dc_solve(M, ZDC, circ, Gmin=None, x0=None, time=None,
             MAXIT=1000, locked_nodes=None):
    
    """
    This function reduces any impedance components into a single matrix
    (this is the M matrix). DC, AC, and source contributions from capacitive
    /inductive elements during a transient are reduced to the Z matrix
    
    The problem is reduced to:
        
        M + N = Z, where N is non-linear contributions
    
    M and ZDC are operated on by the solver objects, before being
    passed to Raphson solve. There are three solvers:
        
        standard solving, Gmin stepping, source stepping
        
    The system is only considered solved if a solver is finished.
    
    """    
    
    M_size = M.shape[0]
    NNODES = circ.get_nodes_number()
    
    if locked_nodes is None:
        locked_nodes = circ.get_locked_nodes()
    
    if Gmin is None:
        Gmin = 0
        # without source stepping and gmin
        solvers = slv.setup_solvers(Gmin=False)
    else:
        solvers = slv.setup_solvers(Gmin=True)

    # if there is no initial guess, we start with 0
    if x0 is not None:
        x =x0
    else:
        x = np.zeros((M_size, 1))

    logging.info("Solving...")
    iters = 0
    
    converged = False
    
    for solver in solvers:
        while (solver.failed is not True) and (not converged):
            logging.info(f"Now solving with: {solver.name}")
            # 1. Operate on the matrices
            M_, Z = solver.operate_on_M_and_ZDC(np.array(M),\
                                    np.array(ZDC), np.array(Gmin))
            # 2. Try to solve with the current solver
            try:
                (x, error, converged, n_iter)\
                    = raphson_solver(x, M_, circ, Z=Z, nv=NNODES, 
                                    locked_nodes=locked_nodes,
                                    time=time, MAXIT=MAXIT)
                # increment iteration
                iters += n_iter
            except ValueError:
                logging.warning("Singular matrix")
                converged, error, x = False, None, None
                solver.fail()
            
            except OverflowError:
                logging.warning("Overflow error detected...")
                converged, error, x = False, None, None
                solver.fail()
            
            if not converged:
                # make sure iterations haven't been exceeded
                if iters == MAXIT - 1:
                    logging.warning("Error: MAXIT exceeded (" + str(MAXIT) + ")")

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

    logging.debug("op_analysis(): constructing Gmin matrix")
    # take away a single node because we have reduced M
    Gmin_matrix = gmin_mat(settings.gmin, M.shape[0], circ.get_nodes_number()-1)
    
    logging.info("op_analysis(): solving with Gmin")
    # now solve
    (x_min, e_min, converged, iters_min) = dc_solve(M, ZDC,
                                              circ, Gmin=Gmin_matrix, x0=x0)
    
    op = results.Solution(circ, outfile, sol_type='OP')
    # convergence specifies a solution, but using Gmin
    if converged:
        logging.info("op_analysis(): now attempting without Gmin:")
        (x, e, solved, iters) = dc_solve(
            M, ZDC, circ, Gmin=None, x0=x_min)
        
        if not solved:
            logging.error("Can't solve without Gmin.")
            logging.warning("Solution is highly dependent on Gmin")
            logging.info("Displaying valid results. Couldn't solve \
                         circuit without Gmin")    
        
        op.write_data(x.transpose().tolist()[0])
        op.close()
        
        return op.as_dict()
        
    logging.critical(f"op_analysis(): No operating point found")
    
    return None


def raphson_solver(x, M, circ, Z, MAXIT, nv, locked_nodes, time=None):

    """
    
    This function solves the non-linear system:
        
        A x + N(x) = Z
    
    if N(x) is zero, the method solves the linear system of equations
    
    """    

    M_size = M.shape[0]
    N = np.zeros((M_size, 1))
    J = np.zeros((M_size, M_size))
    nl = circ.is_nonlinear()
    
    # if no initial estimate is provided, use zeros
    if x is None:
        x = np.zeros((M_size, 1))
    else:
        # bad array from user / previous OP in case of transient
        if x.shape[0] != M_size:
            raise ValueError("x0s size is different from expected: got "
                             "%d-elements x0 with an MNA of size %d" %
                             (x.shape[0], M_size))

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
        error = M.dot(x) + Z + nl*N
        
        LU, INDX, _, C = ludcmp(M + nl*J, M_size)
        if C == 1:
            raise ValueError
        
        dx = lubksb(LU, INDX,  -error)
        # check for overflow error
        if norm(dx) == np.nan:
            raise OverflowError
        
        iters += 1
        # perform newton update
        x = x + get_td(dx, locked_nodes, n=iters) * dx
        
        # if the circuit is linear, we know it has converged upon solution after one iteration
        if not nl:
            converged = True
            break
        # otherwise we need to check it
        else:
            # run the convergence check
            converged, _= convergence_check(
            x, dx, error, nv - 1, debug=True)
            if converged:
                break

    return (x, error, converged, iters)


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
    
    """
    Provide a damping coefficient for the Raphson method
    
    Currently, method damps first 20 iterations
    
    
    
    """
    return 1.0
    if n < 10:
        td = 1e-2
    elif n < 20:
        td = 0.1
    else:
        td = 1
    
    td_new = 1
    
    for (n1, n2) in locked_nodes:
        if n1 != 0:
            if n2 != 0:
                if abs(dx[n1 - 1, 0] - dx[n2 - 1, 0]) > settings.nl_voltages_lock_factor * units.Vth():
                    td_new = (settings.nl_voltages_lock_factor * units.Vth()) / abs(
                        dx[n1 - 1, 0] - dx[n2 - 1, 0])
            else:
                if abs(dx[n1 - 1, 0]) > settings.nl_voltages_lock_factor * units.Vth():
                    td_new = (settings.nl_voltages_lock_factor * units.Vth()) / abs(
                        dx[n1 - 1, 0])
        else:
            if abs(dx[n2 - 1, 0]) > settings.nl_voltages_lock_factor * units.Vth():
                td_new = (settings.nl_voltages_lock_factor * units.Vth()) / abs(
                    dx[n2 - 1, 0])
        if td_new < td:
            td = td_new
    return td

def convergence_check(x, dx, residuum, nv_minus_one, debug=False):
    """Perform a convergence check

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
    nv_minus_one : int
        Number of voltage variables in x. If ``nv_minus_one`` is equal to
        ``n``, it means ``x[:n]`` are all voltage variables.
    debug : boolean, optional
        Whether extra information is needed for debug purposes. Defaults to
        ``False``.

    **Returns:**

    chk : boolean
        Whether the check was passed or not. ``True`` means 'convergence!'.
    rbn : ndarray
        The convergence check results by node, if ``debug`` was set to ``True``,
        else ``None``.
    """
    if not hasattr(x, 'shape'):
        x = np.array(x)
        dx = np.array(dx)
        residuum = np.array(residuum)
    vcheck, vresults = custom_convergence_check(x[:nv_minus_one, 0], dx[:nv_minus_one, 0], residuum[:nv_minus_one, 0], er=settings.ver, ea=settings.vea, eresiduum=settings.iea)
    icheck, iresults = custom_convergence_check(x[nv_minus_one:], dx[nv_minus_one:], residuum[nv_minus_one:], er=settings.ier, ea=settings.iea, eresiduum=settings.vea)
    return vcheck and icheck, vresults + iresults

def custom_convergence_check(x, dx, residuum, er, ea, eresiduum, debug=False):
    """Perform a custom convergence check

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
    ea : float
        The value to be employed for the absolute error.
    er : float
        The value for the relative error to be employed.
    eresiduum : float
        The maximum allowed error for the residuum (left over error).
    debug : boolean, optional
        Whether extra information is needed for debug purposes. Defaults to
        ``False``.

    **Returns:**

    chk : boolean
        Whether the check was passed or not. ``True`` means 'convergence!'.
    rbn : ndarray
        The convergence check results by node, if ``debug`` was set to ``True``,
        else ``None``.
    """
    all_check_results = []
    if not hasattr(x, 'shape'):
        x = np.array(x)
        dx = np.array(dx)
        residuum = np.array(residuum)
    if x.shape[0]:
        if not debug:
            ret = np.allclose(x, x + dx, rtol=er, atol=ea) and \
                  np.allclose(residuum, np.zeros(residuum.shape),
                              atol=eresiduum, rtol=0)
        else:
            for i in range(x.shape[0]):
                if np.abs(dx[i, 0]) < er*np.abs(x[i, 0]) + ea and \
                   np.abs(residuum[i, 0]) < eresiduum:
                    all_check_results.append(True)
                else:
                    all_check_results.append(False)
                if not all_check_results[-1]:
                    break

            ret = not (False in all_check_results)
    else:
        # We get here when there's no variable to be checked. This is because
        # there aren't variables of this type.  Eg. the circuit has no voltage
        # sources nor voltage defined elements. In this case, the actual check
        # is done only by current_convergence_check, voltage_convergence_check
        # always returns True.
        ret = True

    return ret, all_check_results
