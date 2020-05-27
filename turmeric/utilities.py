#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian


This module holds miscellaneous utility functions.

"""

import collections
import os
import os.path

import numpy as np

from functools import wraps

from . import printing
from . import options

#: The machine epsilon, the upper bound on the relative error due to rounding in
#: floating point arithmetic.
EPS = np.finfo(float).eps

def remove_row_and_col(matrix, rrow=0, rcol=0):
    """Removes a row and/or a column from a matrix

    **Parameters:**

    matrix : ndarray
        The matrix to be modified.
    rrow : int or None, optional
        The index of the row to be removed. If set to ``None``, no row
        will be removed. By default the first row is removed.
    rcol : int or None, optional
        The index of the row to be removed. If set to ``None``, no row
        will be removed. By default the first column is removed.

    .. note::

        No size checking is done.

    **Returns:**

    matrix : ndarray
        A reference to the modified matrix.
    """
    if rrow is not None and rcol is not None:
        return np.vstack((np.hstack((matrix[0:rrow, 0:rcol],
                                     matrix[0:rrow, rcol+1:])),
                          np.hstack((matrix[rrow+1:, 0:rcol],
                                     matrix[rrow+1:, rcol+1:]))
                          ))
    elif rrow is not None:
        return np.vstack((matrix[:rrow, :], matrix[rrow+1:, :]))
    elif rcol is not None:
        return np.hstack((matrix[:, :rcol], matrix[:, rcol+1:]))

def expand_matrix(matrix, add_a_row=False, add_a_col=False):
    """Append a row and/or a column to the given matrix

    **Parameters:**

    matrix : ndarray
        The matrix to be manipulated.
    add_a_row : boolean, optional
        If set to ``True`` a row is appended to the supplied matrix.
    add_a_col : boolean
        If set to ``True`` a column is appended.

    **Returns:**

    matrix : ndarray
        A reference to the same matrix supplied.

    """
    n_row, n_col = matrix.shape
    if add_a_col:
        col = np.zeros((n_row, 1))
        matrix = np.concatenate((matrix, col), axis=1)
    if add_a_row:
        if add_a_col:
            n_col = n_col + 1
        row = np.zeros((1, n_col))
        matrix = np.concatenate((matrix, row), axis=0)
    return matrix

def set_submatrix(row, col, dest_matrix, source_matrix):
    """Copies a source matrix into another matrix

    row, col : ints
        The coordinates of the upper left corner in the destination matrix where
        the source matrix will be copied.
    dest_matrix : ndarray
        The matrix to be copied to.
    source_matrix : ndarray
        The matrix to be copied from.

    **Returns:**

    dest_matrix : ndarray
        A reference to the modified destination matrix.
    """
    ls = source_matrix.shape[0]
    cs = source_matrix.shape[1]
    dest_matrix[row:row+ls, col:col+cs] = source_matrix[:, :]
    return dest_matrix


def check_file(filename):
    """Checks whether the supplied path refers to a valid file.

    **Parameters:**

    filename : string
        The file name.

    **Returns:**

    chk : boolean
        A value of ``True`` if ``filename`` is found and it is a file.

    :raises IOError: if no such file exists or if the supplied file is a directory.
    """
    filename = os.path.abspath(filename)
    if not os.path.exists(filename):
        raise IOError(filename + " not found.")
    elif not os.path.isfile(filename):
        raise IOError(filename + " is not a file.")
    return True

def tuplinator(alist):
    """Convert a list of lists (of lists...) to tuples"""
    if type(alist) is list:
        return tuple([tuplinator(i) for i in alist])
    else:
        return alist

class combinations:

    """This class is an iterator that returns all the k-combinations
    _without_repetition_ of the elements of the supplied list.

    Each combination is made of a subset of the list, consisting of k
    elements.

    **Parameters:**

    L : list
        The set from which the elements are taken.
    k : int
        The size of the subset, the number of elements to be taken
    """

    def __init__(self, L, k):
        self.L = L
        self.k = k
        self._sub_iter = None
        self._i = 0
        if len(self.L) < k:
            raise ValueError("The set has to be bigger than the subset.")
        if k <= 0:
            raise ValueError("The size of the subset has to be strictly " +
                             "positive.")

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        # It's recursive
        if self.k > 1:
            if self._sub_iter == None:
                self._sub_iter = combinations(self.L[self._i + 1:], self.k - 1)
            try:
                nxt = self._sub_iter.__next__()
                cur = self.L[self._i]
            except StopIteration:
                if self._i < len(self.L) - self.k:
                    self._i = self._i + 1
                    self._sub_iter = combinations(
                        self.L[self._i + 1:], self.k - 1)
                    return self.__next__()
                else:
                    raise StopIteration
        else:
            nxt = []
            if self._i < len(self.L):
                cur = self.L[self._i]
                self._i = self._i + 1
            else:
                raise StopIteration

        return [cur] + nxt


def Celsius2Kelvin(cel):
    """Convert Celsius degrees to Kelvin
    """
    return cel + 273.15


def Kelvin2Celsius(kel):
    """Convert Kelvin degrees to Celsius
    """
    return kel - 273.15

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
    vcheck, vresults = voltage_convergence_check(x[:nv_minus_one, 0],
                                                 dx[:nv_minus_one, 0],
                                                 residuum[:nv_minus_one, 0])
    icheck, iresults = current_convergence_check(x[nv_minus_one:],
                                                 dx[nv_minus_one:],
                                                 residuum[nv_minus_one:])
    return vcheck and icheck, vresults + iresults


def voltage_convergence_check(x, dx, residuum, debug=False):
    """Perform a convergence check for voltage variables

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
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
    return custom_convergence_check(x, dx, residuum, er=options.ver,
                                    ea=options.vea, eresiduum=options.iea,
                                    debug=debug)


def current_convergence_check(x, dx, residuum, debug=False):
    """Perform a convergence check for current variables

    **Parameters:**

    x : array-like
        The results to be checked.
    dx : array-like
        The last increment from a Newton-Rhapson iteration, solving
        ``F(x) = 0``.
    residuum : array-like
        The remaining error, ie ``F(x) = residdum``
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
    return custom_convergence_check(x, dx, residuum, er=options.ier,
                                    ea=options.iea, eresiduum=options.vea,
                                    debug=debug)


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

def check_step_and_points(step=None, points=None, period=None,
                          default_points=100):
    """Sets consistently the step size and the number of points

    The calculation is done according to the given period.

    **Parameters:**

    step : scalar, optional
        The discretization step.
    points : int, optional
        The number of points to be used in the discretization.
    period : scalar, optional
        The length of the interval to be discretized. Not setting
        this parameter will result in a ``ValueError``.
    default_points : int, optional
        The default number of points.

    **Returns:**

    (points, step) : tuple
        The adjusted number of points and step value.
    """

    if step is None and points is None:
        printing.print_warning("Neither step nor n. of points set. Using %d points." % default_points)
        points = default_points
    elif step is not None and points is not None:
        printing.print_warning("Both step and # of points set. Using step = %f." % step)
        points = None

    if points:
        step = float(period)/(points - 1)
    else:
        points = float(period)/step
        if points % 1 != 0:
            step = step + (step * (points % 1)) / int(points)
            points = int(float(period)/step)
            printing.print_warning("adapted step is %g" % (step,))
        else:
            points = int(points)
        # 0 - N where xN is in reality the first point of the second period!!
        points = points + 1

    return int(points), step

def check_ground_paths(mna, circ, reduced_mna=True, verbose=3):
    """Checks that every node has a DC path to ground

    The path to ground might be through non-linear elements.

    .. note::

        * This does not ensure that the circuit will have a DC solution.
        * A node without DC path to ground would be rescued (likely) by GMIN so
          (for the time being at least) we do *not* halt the execution.
        * Also, two series capacitors always fail this check (GMIN saves us)

    Bottom line: if there is no DC path to ground, there is probably a
    mistake in the netlist. Print a warning.

    **Returns:**

    chk : boolean
        A boolean set to true if there is a DC path to ground from all nodes
        in the circuit.
    """
    test_passed = True
    if reduced_mna:
        # reduced_correction
        r_c = 1
    else:
        r_c = 0
    to_be_checked_for_nonlinear_paths = []
    for node in iter(circ.nodes_dict.keys()):
        if node == 0:
            continue
            # ground
        if type(node) != int:
            # an ext handle
            continue
        if mna[node - r_c, node - r_c] == 0 and \
           not mna[node - r_c, circ.get_nodes_number() - r_c:].any():
            to_be_checked_for_nonlinear_paths.append(node)
    for node in to_be_checked_for_nonlinear_paths:
        node_is_nl_op = False
        for elem in circ:
            if not elem.is_nonlinear:
                continue
            ops = elem.get_output_ports()
            for op in ops:
                if op.count(node):
                    node_is_nl_op = True
        if not node_is_nl_op:
            if verbose:
                printing.print_warning(
                    "No path to ground from node " + circ.nodes_dict[node])
            test_passed = False
    return test_passed

def memoize(f):
    """Memoization decorator

    **Parameters:**

    f : function
        The function to apply memoization to.

    **Returns:**

    fm : function
        The function with added memoization.

    **Implementation:**

    Originally from `this post
    <https://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/#c4>`_,
    it has been modified to provide a cache of size ``options.cache_len``.

    .. note::

        The size of the cache is per model instance and per function. If you
        have one model, shared by several elements, you probably prefer to have
        a big cache.

    """
    class memodict(collections.OrderedDict):
        __slots__ = ()
        @wraps(f)
        def __getitem__(self, *key):
            return dict.__getitem__(self, key)
        def __missing__(self, key):
            ret = self[key] = f(*key)
            # set options.cache_len to None to disable any size limit.
            if options.cache_len is not None and len(self) > options.cache_len:
                self.popitem() #FIFO pop
            return ret
    return memodict().__getitem__


