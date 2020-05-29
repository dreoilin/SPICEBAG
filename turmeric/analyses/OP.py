import logging

from turmeric.FORTRAN.LU import ludcmp, lubksb
from turmeric.FORTRAN.DC_SUBRS import gmin_mat

from numpy.linalg import norm
import numpy as np    

from turmeric import units
from turmeric import settings
from turmeric import solvers as slv
from turmeric import results
from turmeric.components.tokens import ParamDict, Value
from turmeric.analyses.Analysis import Analysis

class OP(Analysis):
    """
    ~~~~~~~~~~~~~~~~~~
    OP Analysis Class:
    ~~~~~~~~~~~~~~~~~~

    Provides a class for the OP analysis of a netlist.
    
    """
    
    def __init__(self, line):
        self.net_objs = [ParamDict.allowed_params(self, optional=True, paramset={
            'x0' : { 'type' : lambda v: [float(val) for val in list(v)], 'default' : [] }})]
        super().__init__(line)
        if not len(self.x0) > 0:
            self.x0 = None

    def __repr__(self):
        """
        .OP [x0=\[<Value>...\]]
        """
        r = f".OP"
        r += ' x0=['+''.join(str(v) for v in self.x0) + ']' if self.x0 is not None else ''
        return r

    def run(self, circ):
        return op_analysis(circ, self.x0)

def op_analysis(circ, x0=None):
    
    """
    ~~~~~~~~~~~~~~~~~~
    OP Analysis Method:
    ~~~~~~~~~~~~~~~~~~
    
    This function is the entry point for an operating point analysis
    The analysis sets up the MNA matrices using a circuit object and constructs
    the Gmin matrix used in the dc solver
    
    A circuit solution is attempted twice:
        - Once with a Gmin matrix and
        - a second time without (to enhance results)
        
    If the analysis cannot find a solution without Gmin, the Gmin solution is
    returned with a warning. In this case, a solution is heavily dependent on
    the minimum conductance to ground.
    
    If the circuit cannot be solved using any of the available solving methods,
    the special value None is returned
    
    x0 is the initial estimate provided by the user
    
    """
    
    logging.debug("op_analysis(): getting and reducing M0 and ZDC0 from circuit")
    
    M = circ.M0[1:, 1:]
    ZDC = circ.ZDC0[1:]
    
    logging.info("op_analysis(): Beginning operating point analysis")

    logging.debug("op_analysis(): constructing Gmin matrix")
    # take away a single node because we have reduced M
    Gmin_matrix = gmin_mat(settings.gmin, M.shape[0], circ.get_nodes_number()-1)
    
    logging.info("op_analysis(): solving with Gmin")
    # now solve
    (x_min, e_min, converged, iters_min) = dc_solve(M, ZDC,
                                              circ, Gmin=Gmin_matrix, x0=x0)
    
    op = results.Solution(circ, sol_type='OP')
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

def dc_solve(M, Z, circ, Gmin=None, x0=None, time=None,
             MAXIT=1000, locked_nodes=None):
    
    """
    M   : the conductance matrix
    Z   : the source matrix
    Gmin : minimim conductance to ground
            Gmin of None disables Gmin and source stepping
    MAXIT : Maximum number iterations for the newton method
    locked_nodes : a list of nodes connected to non-linear (diode) elements
    
    
    This method operates on the MNA matrices using the implemented
    solving techniques before passing them to the low level raphson.
    
        At this point, the system has been reduced to:
        
        M + N = Z, where N is non-linear contributions
    
    M and ZDC are operated on by the solver objects, before being
    passed to Raphson solve. 
    
        We currently have three solvers:
        
        - standard solving - Gmin stepping - source stepping
        
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
        if isinstance(x0, np.ndarray):
            x =x0
        elif isinstance(x0, dict):
            x0 = [value for value in x0.values()]
            x0 = np.array(x0)
    else:
        x = np.zeros((M_size, 1))

    logging.info("Solving...")
    iters = 0
    
    converged = False
    
    for solver in solvers:
        while (solver.failed is not True) and (not converged):
            logging.info(f"Now solving with: {solver.name}")
            # 1. Operate on the matrices
            M_, Z_ = solver.operate_on_M_and_ZDC(np.array(M),\
                                    np.array(Z), np.array(Gmin))
            # 2. Try to solve with the current solver
            try:
                (x, error, converged, n_iter)\
                    = MNA_solve(x, M_, circ, Z=Z_, nv=NNODES, 
                                    locked_nodes=locked_nodes,
                                    time=time, MAXIT=MAXIT)
                # increment iteration
                iters += n_iter
            except SingularityError:
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


def MNA_solve(x, M, circ, Z, MAXIT, nv, locked_nodes, time=None):

    """
    M : conductance matrix
    Z : source matrix
    MAXIT : maximum number of iterations for the newton method
            locked_nodes: list of nodes connected to non-linear elements
    
    Low level method to solve the system MNA equations
    
    This function solves the non-linear system:
        
        A x + N(x) = Z
    
    if N(x) is zero, the method solves the linear system of equations,
    and returns immediately.
    
    If the system is non-linear, it is solved by means of a damped newton
    iteration method.
    
    Damping is configurable in the turmeric config.json file
    
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
            raise ValueError

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
        
        # compute the sum of node voltages and branch currents
        # this is the 'error' -> should sum to 0
        error = M.dot(x) + Z + nl*N
        # now solve the system using LU decomposition
        LU, INDX, _, C = ludcmp(M + nl*J, M_size)
        if C == 1:
            # singularity
            raise SingularityError
        
        dx = lubksb(LU, INDX,  -error)
        # check for overflow error
        if norm(dx) == np.nan:
            raise OverflowError
        
        iters += 1
        # perform newton update and damp appropriately
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


class SingularityError(Exception):
    pass
