#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from . import circuit
from . import dc
from . import components
from . import options
from . import printing
from . import results
from . import utilities
import logging

specs = {'ac': {'tokens': ({
                           'label': 'type',
                           'pos': 0,
                           'type': str,
                           'needed': False,
                           'dest': 'sweep_type',
                           'default': options.ac_log_step
                           },
                          {
                           'label': 'nsteps',
                           'pos': 1,
                           'type': float,
                           'needed': True,
                           'dest': 'points',
                           'default': None
                          },
                          {
                           'label': 'start',
                           'pos': 2,
                           'type': float,
                           'needed': True,
                           'dest': 'start',
                           'default': None
                          },
                          {
                           'label': 'stop',
                           'pos': 3,
                           'type': float,
                           'needed': True,
                           'dest': 'stop',
                           'default': None
                          })
               }
        }


def ac_analysis(circ, start, points, stop, sweep_type=None,
                x0=None, AC=None, outfile="stdout"):

    
    # check step/start/stop parameters
    if start == 0:
        raise ValueError("AC analysis has start frequency = 0")
    if start > stop:
        raise ValueError("AC analysis has start > stop")
    if points < 2 and not start == stop:
        raise ValueError("AC analysis has number of points < 2 & start != stop")
    if sweep_type.upper() == options.ac_log_step or sweep_type is None:
        omega_iter = utilities.log_axis_iterator(2*np.pi*start, 2*np.pi*stop, points)
    elif sweep_type.upper() == options.ac_lin_step:
        omega_iter = utilities.lin_axis_iterator(2*np.pi*start, 2*np.pi*stop, points)
    else:
        raise ValueError("Unknown sweep type %s" % sweep_type)


    logging.info("Starting AC analysis: ")
    logging.info("w: start = %g Hz, stop = %g Hz, %d points" % (start, stop, points))
    
    #if mna is None:
    #    mna, N = dc.generate_mna_and_N(circ, verbose=verbose)
    #    del N
    #    mna = utilities.remove_row_and_col(mna)
    #if Nac is None:
    #    Nac = _generate_Nac(circ)
    #    Nac = utilities.remove_row(Nac, rrow=0)
    #if AC is None:
    #    AC = _generate_AC(circ, [mna.shape[0], mna.shape[0]])
    #    AC = utilities.remove_row_and_col(AC)

    if circ.is_nonlinear():
        if x0 is None:
            #msg = "No initial estimate provided"    
            #logging.info( +
            #                              "linearization point...", 3), verbose,
            #                             print_nl=False)
                # silent OP
            x0 = dc.op_analysis(circ, verbose=0)
            if x0 is None:  # still! Then op_analysis has failed!
                logging.info("failed.")
                raise RuntimeError("OP analysis failed, no " +
                                       "linearization point available.")
            else:
                    logging.info("done.")
            logging.info("Linearization point (xop):")
            J = _generate_J(xop=x0.asarray(), circ=circ,
                            reduced_mna_size=mna.shape[0])
            logging.info(" done.")
            # we have J, continue
    else:  # not circ.is_nonlinear()
        # no J matrix is required.
        J = 0

    printing.print_info_line(("MNA (reduced):", 5), verbose)
    printing.print_info_line((mna, 5), verbose)
    printing.print_info_line(("AC (reduced):", 5), verbose)
    printing.print_info_line((AC, 5), verbose)
    printing.print_info_line(("J (reduced):", 5), verbose)
    printing.print_info_line((J, 5), verbose)
    printing.print_info_line(("Nac (reduced):", 5), verbose)
    printing.print_info_line((Nac, 5), verbose)

    sol = results.ac_solution(circ, start=start, stop=stop, points=points,
                              stype=sweep_type, op=x0, outfile=outfile)

    # setup the initial values to start the iteration:
    j = np.complex('j')

    Gmin_matrix = dc.build_gmin_matrix(
        circ, options.gmin, mna.shape[0], verbose)

    iter_n = 0  # contatore d'iterazione
    printing.print_info_line(("Solving... ", 3), verbose, print_nl=False)

    x = x0
    for omega in omega_iter:
        x, _, solved, _ = dc.dc_solve(
            mna=(mna + np.multiply(j * omega, AC) + J),
            Ndc = Nac,
            Ntran = 0,
            circ = circuit.Circuit(
                title="Dummy circuit for AC", filename=None),
            Gmin = Gmin_matrix,
            x0 = x,
            time = None,
            locked_nodes = None,
            MAXIT = options.ac_max_nr_iter,
            skip_Tt = True,
            verbose = 0)
        if solved:
            iter_n = iter_n + 1
            # hooray!
            sol.add_line(omega/np.pi/2, x)
        else:
            break

    if solved:
        printing.print_info_line(("done.", 1), verbose)
        ret_value = sol
    else:
        printing.print_info_line(("failed.", 1), verbose)
        ret_value = None

    return ret_value


def _generate_AC(circ, shape):
    """Generates the AC coefficients matrix.

    **Parameters:**

    circ : Circuit instance
        The circuit instance for which the :math:`AC` matrix will be generated.

    shape : int
        The reduced MNA size.

    **Returns:**

    AC : ndarray
        The *unreduced* (full size) :math:`AC` matrix.

    """
    AC = np.zeros((shape[0] + 1, shape[1] + 1))
    nv = circ.get_nodes_number()  # - 1
    i_eq = 0  # each time we find a vsource or vcvs or ccvs, we'll add one to this.
    for elem in circ:
        if circuit.is_elem_voltage_defined(elem) and not isinstance(elem, components.Inductor):
            i_eq = i_eq + 1
        elif isinstance(elem, components.Capacitor):
            n1 = elem.n1
            n2 = elem.n2
            AC[n1, n1] = AC[n1, n1] + elem.value
            AC[n1, n2] = AC[n1, n2] - elem.value
            AC[n2, n2] = AC[n2, n2] + elem.value
            AC[n2, n1] = AC[n2, n1] - elem.value
        elif isinstance(elem, components.Inductor):
            AC[nv + i_eq, nv + i_eq] = -1 * elem.value
            if len(elem.coupling_devices):
                for cd in elem.coupling_devices:
                    # get `part_id` of the other inductor (eg. "L32")
                    other_id_wdescr = cd.get_other_inductor(elem.part_id)
                    # find its index to know which column corresponds to its
                    # current
                    other_index = circ.find_vde_index(
                        other_id_wdescr, verbose=0)
                    # add the term.
                    AC[nv + i_eq, nv + other_index] += -1 * cd.M
            i_eq = i_eq + 1

    if options.cmin > 0:
        cmin_mat = np.eye(shape[0] + 1 - i_eq)
        cmin_mat[0, 1:] = 1
        cmin_mat[1:, 0] = 1
        cmin_mat[0, 0] = cmin_mat.shape[0] - 1
        if i_eq:
            AC[:-i_eq, :-i_eq] += options.cmin * cmin_mat
        else:
            AC += options.cmin * cmin_mat

    return AC


def _generate_Nac(circ):
    """Generate the vector holding the contribution of AC sources.

    **Parameters:**

    circ : Circuit instance
        The circuit instance for which the :math:`N_{ac}` matrix will be
        generated.

    **Returns:**

    Nac : ndarray
        The constant term :math:`N_{ac}`.
    """
    n_of_nodes = circ.get_nodes_number()
    Nac = np.zeros((n_of_nodes, 1), dtype=complex)
    j = np.complex('j')
    # process `ISource`s
    for elem in circ:
        if isinstance(elem, components.sources.ISource) and elem.abs_ac is not None:
            # convenzione normale!
            Nac[elem.n1, 0] = Nac[elem.n1, 0] + \
                elem.abs_ac * np.exp(j * elem.arg_ac)
            Nac[elem.n2, 0] = Nac[elem.n2, 0] - \
                elem.abs_ac * np.exp(j * elem.arg_ac)
    # process vsources
    # for each vsource, introduce a new variable: the current flowing through it.
    # then we introduce a KVL equation to be able to solve the circuit
    for elem in circ:
        if circuit.is_elem_voltage_defined(elem):
            index = Nac.shape[0]
            Nac = utilities.expand_matrix(Nac, add_a_row=True, add_a_col=False)
            if isinstance(elem, components.sources.VSource) and elem.abs_ac is not None:
                Nac[index, 0] = -1.0 * elem.abs_ac * np.exp(j * elem.arg_ac)
    return Nac


def _generate_J(xop, circ, reduced_mna_size):
    """Build the linearized matrix :math:`J`

    **Parameters:**

    xop : ndarray
        The linearization point, as a ``numpy`` ndarray.
    circ : Circuit instance
        The circuit for which :math:`J` is to be generated.
    reduced_mna_size : int
        The size of the (square) Modified Nodal Analysis Matrix, after
        reduction.

    **Returns:**

    J : ndarray of size ``(reduced_mna_size, reduced_mna_size)``
        The reduced Jacobian :math:`J`.

    """
    # setup J
    J = np.zeros((reduced_mna_size, reduced_mna_size))
    Tlin = np.zeros((reduced_mna_size, 1))
    for elem in circ:
        if elem.is_nonlinear:
            dc._update_J_and_Tx(J, Tlin, xop, elem, time=None)
    # del Tlin # not needed! **DC**!
    return J
