#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

import contextlib
import sys
import os

import tabulate as _tabulate
import numpy as np

from . import options


def open_utf8(filename):
    
    fp = open(filename, 'w', encoding='UTF-8')
    return fp

def print_analysis(an):
    """Prints an analysis to ``stdout`` in the netlist syntax

    **Parameters:**

    an : dict
        An analysis description in dictionary format.

    """
    if an["type"] == "op":
        print(".op", end="")
        for x in an:
            if x == 'type' or x == 'outfile' or x == 'verbose':
                continue
            print(" %s=%s" % (x, an[x]), end="")
        print("")
    elif an["type"] == "dc":
        print(".dc %(source)s start=%(start)g stop=%(stop)g step=%(step)g type=%(sweep_type)s" % an)
    elif an["type"] == "tran":
        sys.stdout.write(".tran tstep=" + str(an["tstep"]) + " tstop=" + str(
            an["tstop"]) + " tstart=" + str(an["tstart"]))
        if an["method"] is not None:
            print(" method=" + an["method"])
        else:
            print("")
    elif an["type"] == "shooting":
        sys.stdout.write(".shooting period=" + str(
            an["period"]) + " method=" + str(an["method"]))
        if an["points"] is not None:
            sys.stdout.write(" points=" + str(an["points"]))
        if an["step"] is not None:
            sys.stdout.write(" step=" + str(an["step"]))
        print(" autonomous=", an["autonomous"])


def print_general_error(description, print_to_stdout=False):
    """Prints an error message to ``stderr``

    **Parameters:**

    description : str
        The error description.

    print_to_stdout : bool, optional
        When set to ``True``, printing to ``stdout`` instead of ``stderr``.
        Defaults to ``False``.

    """
    the_error_message = "E: " + description
    if print_to_stdout:
        print(the_error_message)
    else:
        sys.stderr.write(the_error_message + "\n")
    return None


def print_warning(description, print_to_stdout=False):
    """Prints a warning message to ``stderr``

    **Parameters:**

    description : str
        The warning message.

    print_to_stdout : bool, optional
        When set to ``True``, printing to ``stdout`` instead of ``stderr``.
        Defaults to ``False``.

    """
    the_warning_message = "W: " + description
    if print_to_stdout:
        print(the_warning_message)
    else:
        sys.stderr.write(the_warning_message + "\n")
    return None


def print_info_line(msg_relevance_tuple, verbose, print_nl=True):
    """Conditionally print out a message

    **Parameters:**

    msg_relevance_tuple : sequence
        A tuple or list made of ``msg`` and ``importance``, where ``msg`` is a
        string, containing the information to be displayed to the user, and
        ``importance``, an integer, is its importance level. Zero corresponds to
        the highest possible importance level, which is always printed out by
        the simple algorithm discussed below.
    verbose : int
        The verbosity level of the program execution. Admissible levels are in
        the 0-6 range.
    print_nl : boolean, optional
        Whether a new line character should be appended or not to the string
        ``msg`` described above, if it's printed out. Defaults to ``True``.

    **Algorithm selecting when to print:**

    The message ``msg`` is printed out if the verbosity level is greater or
    equal than its importance.
    """
    msg, relevance = msg_relevance_tuple
    if verbose >= relevance:
        with printoptions(precision=options.print_precision,
                          suppress=options.print_suppress):
            if print_nl:
                print(msg)
            else:
                print(msg, end=' ')
                sys.stdout.flush()


def print_parse_error(nline, line, print_to_stdout=False):
    """Prints a parsing error to ``stderr``

    **Parameters:**

    nline : int
        The number of the line on which the error occurred.

    line : str
        The line of the file with the error.

    print_to_stdout : bool, optional
        When set to ``True``, printing to ``stdout`` instead of ``stderr``.
        Defaults to ``False``.

    """
    print_general_error(
        "Parse error on line " + str(nline) + ":", print_to_stdout)
    if print_to_stdout:
        print(line)
    else:
        sys.stderr.write(line + "\n")
    return None

def print_result_check(badvars, verbose=2):
    """Prints out the results of an OP check

    It assumes one set of results is calculated with :math:`G_{min}`, the other
    without.

    **Parameters:**

    badvars : list
        The list returned by :func:`results.op_solution.gmin_check`.
    verbose : int, optional
        The verbosity level, from 0 (silent) to 6.

    """
    if len(badvars):
        print("Warning: solution is heavily dependent on gmin.")
        print("Affected variables:")
        for bv in badvars:
            print(bv)
    else:
        if verbose:
            print("Difference check within margins.")
            print("(Voltage: er=" + str(options.ver) + ", ea=" + str(options.vea) + \
                ", Current: er=" + \
                str(options.ier) + ", ea=" + str(options.iea) + ")")
    return None


def table(data, *args, **argsd):
    
    return _tabulate.tabulate(data, *args, **argsd)

@contextlib.contextmanager
def printoptions(*args, **kwargs):
    """A context manager for ``numpy.set_printoptions``"""
    original = np.get_printoptions()
    np.set_printoptions(*args, **kwargs)
    yield
    np.set_printoptions(**original)

locale = os.getenv('LANG')
if not locale:
    print_warning('Locale appears not set! please export LANG="en_US.UTF-8" or'
                  ' equivalent, ')
    print_warning('or ahkab\'s unicode support is broken.')

