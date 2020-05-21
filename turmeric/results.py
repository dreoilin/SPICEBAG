#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

import sys
import time
import re

import numpy as np

from . import circuit
from . import components
from . import printing
from . import options
from . import constants
from . import csvlib

csvlib.SEPARATOR = "\t"

class _mutable_data(object):
    def __init__(self):
        self._init_file_done = False
    def _add_data(self, data):
        """Add the data matrix to the results set."""
        csvlib.write_csv(self.filename, data, self.variables, append=self._init_file_done)
        self._init_file_done = True


class solution(object):
    """Base class storing a set of generic simulation results.

    This class is not meant to be accessed directly, rather it is
    subclassed by the classes for the specific simulation solutions.

    **Parameters:**

    circ : circuit instance
        the circuit instance of the simulated circuit.
    outfile : string
        the filename of the save file
    """
    def __init__(self, circ, outfile):
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.netlist_file = circ.filename
        self.netlist_title = circ.title
        self.vea = options.vea
        self.ver = options.ver
        self.iea = options.iea
        self.ier = options.ier
        self.gmin = options.gmin
        self.cmin = options.cmin
        self.temp = constants.T
        self.filename = outfile
        self._init_file_done = False

        self.skip_nodes_list = []
        self.variables = []
        self.units = case_insensitive_dict()
        self.iter_index = 0
        self.sol_type = None

    def asarray(self):
        
        data, _, _, _ = csvlib.load_csv(self.filename, load_headers=[],
                                        verbose=0)
        return data

    def __len__(self):
        """Get the number of variables in the results set."""
        return len(self.variables)

    def __getitem__(self, name):
        """Get a specific variable, as from a dictionary."""
        # data, headers, pos, EOF = csvlib.load_csv(...)
        try:
            data, _, _, _ = csvlib.load_csv(self.filename, load_headers=[name],
                                            nsamples=None, skip=0, verbose=0)
        except ValueError:
            raise KeyError(name)
        return data.reshape((-1,))

    def get(self, name, default=None):
        """Get a solution by variable name."""
        try:
            # data, headers, pos, EOF = csvlib.load_csv(...)
            data, _, _, _ = csvlib.load_csv(self.filename, load_headers=[name],
                                            nsamples=None, skip=0, verbose=0)
        except ValueError:
            return default
        return data.reshape((-1,))

    def has_key(self, name):
        """Determine whether the result set contains a variable."""
        return name.upper() in [v.upper() for v in self.variables]

    def __contains__(self, name):
        """Determine whether the result set contains a variable."""
        return name.upper() in [v.upper() for v in self.variables]

    def keys(self):
        """Get all of the results set's variables names."""
        return self.variables

    def values(self):
        """Get all of the results set's variables values."""
        # data, headers, pos, EOF = csvlib.load_csv(...)
        data, _, _, _ = csvlib.load_csv(self.filename,
                                        load_headers=self.variables,
                                        nsamples=None, skip=0, verbose=0)
        values = [data[i, :] for i in range(data.shape[0])]
        return values

    def items(self):
        return list(zip(self.keys(), self.values()))

    # iterator methods
    def __iter__(self):
        self.iter_index = 0
        self.iter_data, self.iter_headers, _, _ = csvlib.load_csv(self.filename)
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.iter_index == len(self.iter_headers):
            self.iter_index = 0
            raise StopIteration
        else:
            next_i = self.iter_headers[self.iter_index]
            if hasattr(self.iter_data, 'shape'):
                next_d = self.iter_data[self.iter_index, :]
            else:
                next_d = self.iter_data[self.iter_index]
            nxt = next_i, next_d
            self.iter_index += 1
        return nxt

class op_solution(solution, _mutable_data):
    """OP results

    **Parameters:**

    x : ndarray
        the result set
    error : ndarray
        the residual error after solution,
    circ : circuit instance
        the circuit instance of the simulated circuit
    outfile: str
        the file to write the results to.
        Use "stdout" to write to std output.
    iterations, int, optional
        The number of iterations needed for convergence, if known.
    """
    def __init__(self, x, error, circ, outfile, iterations=0):
        solution.__init__(self, circ, outfile)
        self.sol_type = "OP"
        self.iterations = iterations

        nv_1 = circ.get_nodes_number() - 1
        self.results = case_insensitive_dict()
        self.errors = case_insensitive_dict()
        self.x = x

        for index in range(nv_1):
            varname = ("V" + str(circ.nodes_dict[index + 1])).upper()
            self.variables += [varname]
            self.results.update({varname: x[index, 0]})
            self.errors.update({varname: error[index, 0]})
            self.units.update({varname: "V"})
            if circ.is_int_node_internal_only(index+1):
                self.skip_nodes_list.append(index)

        index = nv_1 - 1
        for elem in circ:
            if circuit.is_elem_voltage_defined(elem):
                index = index + 1
                varname = ("I("+elem.part_id.upper()+")").upper()
                self.variables += [varname]
                self.results.update({varname: x[index, 0]})
                self.errors.update({varname: error[index, 0]})
                self.units.update({varname: "A"})

        self._op_keys, self._op_info, self.tot_power = self._get_elements_op(circ, x)

    def __str__(self):
        str_repr = \
            (("OP simulation results for '%s'" % (self.netlist_title,)) +
            ('(netlist %s)'%(self.netlist_file,) if self.netlist_file else '') +
            ('.\nRun on %s, data file %s.\n' % \
             (self.timestamp, self.filename)))
        return str_repr + self.get_table_array()

    def __getitem__(self, name):
        """Get a specific variable, as from a dictionary."""
        if not name.upper() in [v.upper() for v in self.variables]:
            raise KeyError
        his = csvlib.get_headers_index(self.variables, [name], verbose=0)
        return self.x[his]

    def get(self, name, default=None):
        """Get a solution by variable name."""
        try:
            data = self.__getitem__(name)
        except KeyError:
            return default
        return data

    def asarray(self):
        """Get all data as a ``numpy`` array"""
        return self.x

    def get_table_array(self):
        headers = ("Variable", "Units", "Value", "Error", "%")
        table = []
        for v in self.variables:
            if self.results[v] != 0:
                relerror = self.errors[v]/self.results[v]*100.0
            else:
                relerror = 0.0
            line = (v, self.units[v], self.results[v], self.errors[v], '%d' %
                    relerror)
            table.append(line)
        return printing.table(table, headers=headers)

    def _get_elements_op(self, circ, x):
        """Returns"""
        tot_power = 0
        i_index = 0
        nv_1 = circ.get_nodes_number() - 1
        op_info = {}
        op_keys = {}
        for elem in circ:
            ports_v_v = []
            if hasattr(elem, "get_op_info"):
                if elem.is_nonlinear:
                    # build the drive ports vector
                    oports = elem.get_output_ports()
                    for index in range(len(oports)):
                        dports = elem.get_drive_ports(index)
                        ports_v = []
                        for port in dports:
                            tempv = 0
                            if port[0]:
                                tempv = x[port[0]-1]
                            if port[1]:
                                tempv = tempv - x[port[1]-1]
                            ports_v.append(tempv)
                    ports_v_v.append(ports_v)
                else:
                    port = (elem.n1, elem.n2)
                    tempv = 0
                    if port[0]:
                        tempv = x[port[0]-1]
                    if port[1]:
                        tempv = tempv - x[port[1]-1]
                    ports_v_v = ((tempv,),)
                if circuit.is_elem_voltage_defined(elem):
                    i = circ.find_vde_index(elem.part_id)
                    nv_1 = circ.get_nodes_number() - 1
                    opk, opi = elem.get_op_info(ports_v_v, x[nv_1 + i])
                else:
                    opk, opi = elem.get_op_info(ports_v_v)
                if elem.part_id[0].upper() != 'M':
                    if elem.part_id[0].upper() in op_info:
                        op_info.update({elem.part_id[0].upper():
                                        op_info[elem.part_id[0].upper()]+[opi]})
                        #assert set(opk) == set(op_keys[elem.part_id[0].upper()])
                    else:
                        op_info.update({elem.part_id[0].upper():[opi]})
                        op_keys.update({elem.part_id[0].upper():[opk]})
                else:
                    op_info.update({elem.part_id.upper():opi})
                    op_keys.update({elem.part_id.upper():[[]]})

            if isinstance(elem, components.sources.GISource):
                v = 0
                v = v + x[elem.n1-1] if elem.n1 != 0 else v
                v = v - x[elem.n2-1] if elem.n2 != 0 else v
                vs = 0
                vs = vs + x[elem.n1-1] if elem.sn1 != 0 else vs
                vs = vs - x[elem.n2-1] if elem.sn2 != 0 else vs
                tot_power = tot_power - v*vs*elem.alpha
            elif isinstance(elem, components.sources.ISource):
                v = 0
                v = v + x[elem.n1-1] if elem.n1 != 0 else v
                v = v - x[elem.n2-1] if elem.n2 != 0 else v
                tot_power = tot_power - v*elem.I()
            elif isinstance(elem, components.sources.VSource) or \
                 isinstance(elem, components.sources.EVSource):
                v = 0
                v = v + x[elem.n1-1] if elem.n1 != 0 else v
                v = v - x[elem.n2-1] if elem.n2 != 0 else v
                tot_power = tot_power - v*x[nv_1 + i_index, 0]
                i_index = i_index + 1
            elif isinstance(elem, components.sources.FISource):
                local_i_index = 0
                found_source = False
                for e in circ:
                    if circuit.is_elem_voltage_defined(e):
                        if isinstance(e, components.sources.VSource) and e.part_id.lower() == elem.source_id.lower():
                            found_source = True
                            break
                        else:
                            local_i_index += 1
                if not found_source:
                    raise RuntimeError("Sensing voltage source %s for %s not found. BUG!" %
                                       (elem.source_id, elem.part_id))
                v = 0.
                v = v + x[elem.n1 - 1] if elem.n1 != 0 else v
                v = v - x[elem.n2 - 1] if elem.n2 != 0 else v
                tot_power = tot_power - v * elem.alpha * x[nv_1 + local_i_index, 0]
            elif isinstance(elem, components.sources.HVSource):
                try:
                    local_i_index = circ.find_vde_index(elem.source_id)
                except ValueError:
                    raise RuntimeError("Sensing voltage source %s for %s not found. BUG!" %
                                       (elem.source_id, elem.part_id))
                local_i_index2 = circ.find_vde_index(elem.part_id)
                tot_power = tot_power - elem.alpha*x[nv_1 + local_i_index, 0]* \
                                        x[nv_1 + local_i_index2, 0]
            elif circuit.is_elem_voltage_defined(elem):
                i_index = i_index + 1

        #op_info.append("TOTAL POWER: %e W\n" % (tot_power,))
        return op_keys, op_info, tot_power

    def write_to_file(self, filename=None):
        if filename is None and self.filename is None:
            # maybe warn the user here?
            return
        if filename is None:
            filename = self.filename
        if filename != 'stdout':
            fp = printing.open_utf8(filename+"info")
        else:
            fp = sys.stdout
        fp.write(self.timestamp+"\n")
        fp.write("Operating Point (OP) analysis\n\n")
        fp.write("Netlist: %s\nTitle: %s\n" % (self.netlist_file, self.netlist_title))
        fp.write("At %.2f K\n" % (self.temp,))
        fp.write("Options:\n\tvea = %e\n\tver = %f\n\tiea = %e\n\tier = %f\n\tgmin = %e\n" \
                 % (self.vea, self.ver, self.iea, self.ier, self.gmin))
        fp.write("\nConvergence reached in %d iterations.\n" % (self.iterations,))
        fp.write("\n========\n")
        fp.write("RESULTS:\n")
        fp.write("========\n\n")
        vtable = self.get_table_array()
        fp.write(vtable+'\n')
        fp.write("\n========================\n")
        fp.write("ELEMENTS OP INFORMATION:\n")
        fp.write("========================\n\n")
        for k in sorted(self._op_info.keys()):
            t = printing.table(self._op_info[k], headers=self._op_keys[k][0])
            fp.write(t + '\n\n')
        fp.write('Total power dissipation: %g W\n\n' % self.tot_power)
        fp.flush()
        if filename != 'stdout':
            fp.close()
            # save to .op file
            self._add_data(self.x)

    def print_short(self):
        """Print a short, essential representation of the OP results"""
        table = []
        line = []
        for v in self.variables:
            line.append("%s: %g %s" % \
                        (v, self.results[v], self.units[v]))
            if len(line) == 5:
                table.append(line)
                line = []
        if len(line) > 0: # add the last line
            line += [""]*(5 - len(line))
            table.append(line)
        print(printing.table(table))

    @staticmethod
    def gmin_check(op2, op1):
        """Checks the differences between two sets of OP results.

        It is assumed that one set of results is calculated with Gmin, the other without.

        **Parameters:**

        op1, op2: op_solution instances
            the results vectors, interchangeable

        **Returns:**

        test_fail_variables : list
            The list of the variables that did not pass the test. They are extracted from
            the op_solution objects. If the check was passed, this is an empty list.
        """

        check_failed_vars = []
        for v in op1.variables:
            abserr = abs(op2.results[v] - op1.results[v])
            if op1.units[v] == 'V':
                if abserr > options.ver*max(abs(op1.results[v]),
                                            abs(op2.results[v])) + options.vea:
                    check_failed_vars.append(v)
            elif op1.units[v] == 'A':
                if abserr > options.ier*max(abs(op1.results[v]),
                                            abs(op2.results[v])) + options.iea:
                    check_failed_vars.append(v)
            else:
                print("Unrecognized unit... Bug.")
        return check_failed_vars

    def values(self):
        """Get all of the results set's variables values."""
        return np.squeeze(self.x).tolist()

    def items(self):
        vlist = []
        for j in range(self.x.shape[0]):
            vlist.append(self.x[j, 0])
        return list(zip(self.variables, vlist))

    # iterator methods
    def __iter__(self):
        self._iter_index = 0
        return self

    def next(self):
        if self._iter_index == len(self.variables):
            self._iter_index = 0
            raise StopIteration
        else:
            nxt = self.variables[self._iter_index], \
                   self.x[self._iter_index]
            self._iter_index += 1
        return nxt

    def __next__(self):
        return self.next()


class ac_solution(solution, _mutable_data):
    """AC results

    **Parameters:**

    circ : circuit instance
        the circuit instance of the simulated circuit
    start : float
       the AC sweep frequency start value, in Hz.
    stop : float
       the AC sweep frequency stop value, in Hz.
    points : int
       the AC sweep total points.
    stype : str
       the type of sweep, ``"LOG"``, ``"LIN"`` or arb. ``"POINTS"``.
    op : op_solution
       the linearization Operating Point used to compute the results.
    outfile: str
        the file to write the results to.  Use ``"stdout"`` to write to the
        standard output.
    """
    def __init__(self, circ, start, stop, points, stype, op, outfile):
        solution.__init__(self, circ, outfile)
        self.sol_type = "AC"
        self.linearization_op = op
        self.stype = stype
        self.ostart, self.ostop, self.opoints = start, stop, points

        self.variables += ["f"]
        self.units.update({"f": "Hz"})
        self.csv_headers = [self.variables[0]]

        nv_1 = circ.get_nodes_number() - 1 # numero di soluzioni di tensione (al netto del ref)
        for index in range(nv_1):
            varname = "V%s" % str(circ.nodes_dict[index + 1])
            self.variables += [varname]
            self.units.update({varname: "V"})
            if circ.is_int_node_internal_only(index+1):
                self.skip_nodes_list.append(index)

        for elem in circ:
            if circuit.is_elem_voltage_defined(elem):
                varname = "I(%s)" % elem.part_id.upper()
                self.variables += [varname]
                self.units.update({varname: "A"})

        for i in range(1, len(self.variables)):
            self.csv_headers.append("|%s|" % self.variables[i])
            self.csv_headers.append("arg(%s)" % self.variables[i])

    def _add_data(self, data):
        """Remember to call this method with REAL data - already split in ABS and PHASE."""
        csvlib.write_csv(self.filename, data, self.csv_headers, append=self._init_file_done)
        self._init_file_done = True

    def __str__(self):
        return ("<AC simulation results for '%s' (netlist %s). %s sweep, " +
                "from %g to %g rad/sec, %d points. Run on %s, data file " +
                "%s>") % (self.netlist_title, self.netlist_file, self.stype,
                          self.ostart, self.ostop, self.opoints, self.timestamp,
                          self.filename)

    def add_line(self, frequency, x):
        frequency = np.array([[frequency]])
        xsplit = np.zeros((x.shape[0]*2, 1))
        for i in range(x.shape[0]):
            xsplit[2*i, 0] = np.abs(x[i, 0])
            xsplit[2*i+1, 0] = np.angle(x[i, 0], deg=options.ac_phase_in_deg)

        data = np.concatenate((frequency, xsplit), axis=0)
        self._add_data(data)

    def get_x(self):
        return self[self.variables[0]]

    def get_xlabel(self):
        return self.variables[0]

    def asarray(self):
        """Return all data as a (possibly huge) python matrix."""
        ## data, headers, pos, EOF = csvlib.load_csv()
        data, headers, _, _ = csvlib.load_csv(self.filename, load_headers=[],
                                              nsamples=None, skip=0, verbose=0)
        cplx_data = None
        cplx_headers = []
        re1 = '\\|(.*?)\\|'
        rg = re.compile(re1, re.IGNORECASE|re.DOTALL)

        for i in range(len(headers)):
            if headers[i].upper() == self.variables[0].upper():
                if cplx_data is None:
                    cplx_data = np.array(data[i, :].reshape((1, -1)), dtype=np.complex_)
                else:
                    cplx_data = np.vstack((cplx_data, data[i, :].reshape((1, -1))))
            else:
                m = rg.search(headers[i])
                if m: # we got a |VAR|
                    var = m.group(1)
                    cplx_headers.append(var)
                    match_phase = ('arg(%s)' % var).upper()
                    ip = [h.upper() for h in headers].index(match_phase)
                    if cplx_data is None:
                        cplx_data = np.array(data[i, :]*
                                             np.exp(1j*data[ip,:]).reshape((1, -1)),
                                             dtype=np.complex_)
                    else:
                        cplx_data = np.vstack((cplx_data,
                                               (data[i, :]*
                                                np.exp(1j*data[ip, :])).reshape((1, -1))))
        return cplx_data

    # Access as a dictionary BY VARIABLE NAME:
    def __getitem__(self, name):
        """Get a specific variable, as from a dictionary."""
        if name.upper() != 'F':
            headers = ['|%s|' % name, 'arg(%s)' % name]
        else:
            headers = [name]
        try:
            # data, headers, pos, EOF = csvlib.load_csv()
            data, headers, _, _ = csvlib.load_csv(self.filename,
                                                  load_headers=headers,
                                                  nsamples=None, skip=0,
                                                  verbose=0)
        except ValueError:
            # raise the correct exception
            raise KeyError(name)
        if len(headers) == 2:
            data = data[0, :] * np.exp(1j*data[1, :])
        else:
            data = data.reshape((-1,))
        return data

    def get(self, name, default=None):
        """Get a solution by variable name."""
        try:
            data = self.__getitem__(name)
        except KeyError:
            return default
        return data

    def values(self):
        """Get all of the results set's variables values."""
        data = self.asarray()
        values = [np.real_if_close(data[0, :])]
        for i in range(1, data.shape[0]):
            values.append(data[i, :])
        return values

    def items(self):
        values = self.values()
        return zip(self.variables, values)

    # iterator methods
    def __iter__(self):
        self.iter_index = 0
        self.iter_data = self.values()
        self.iter_headers = self.variables
        return self

class dc_solution(solution, _mutable_data):
    """DC results

       **Parameters:**

       circ : circuit instance
           the simulated circuit.
       start : float
           the DC sweep start value.
       stop : float
           the DC sweep stop value.
       sweepvar : str
           the swept variable ``part_id``.
       stype : str
           the type of sweep, ``"LOG"``, ``"LIN"`` or arb. ``"POINTS"``.
       outfile : str
           the filename of the file where the results will be written.
           Use ``"stdout"`` to write to std output.
    """
    def __init__(self, circ, start, stop, sweepvar, stype, outfile):
        solution.__init__(self, circ, outfile)
        self.sol_type = "DC"
        self.start, self.stop = start, stop
        self.stype = stype

        nv_1 = circ.get_nodes_number() - 1 # numero di soluzioni di tensione (al netto del ref)
        self.variables = [sweepvar]
        self.units = case_insensitive_dict()
        if self.variables[0][0] == 'V':
            self.units.update({self.variables[0]:'V'})
        if self.variables[0][0] == 'I':
            self.units.update({self.variables[0]:'A'})

        for index in range(nv_1):
            varname = "V%s" % (str(circ.nodes_dict[index + 1]),)
            self.variables += [varname]
            self.units.update({varname:"V"})
            if circ.is_int_node_internal_only(index+1):
                self.skip_nodes_list.append(index)

        for elem in circ:
            if circuit.is_elem_voltage_defined(elem):
                varname = "I(%s)" % (elem.part_id.upper(),)
                self.variables += [varname]
                self.units.update({varname:"A"})

    def __str__(self):
        return ("<DC simulation results for '%s' (netlist %s). %s sweep of" +
                " %s from %g to %g %s. Run on %s, data file %s>") % \
               (self.netlist_title, self.netlist_file, self.stype,
                self.variables[0].upper(), self.start, self.stop,
                self.units[self.variables[0]], self.timestamp, self.filename)

    def add_op(self, sweepvalue, op):
        """A DC sweep is made of a set of OP points.

        This method adds an OP solution and
        its corresponding sweep value to the results set.
        """
        sweepvalue = np.array([[sweepvalue]])
        x = op.asarray()
        data = np.concatenate((sweepvalue, x), axis=0)
        self._add_data(data)

    def get_x(self):
        return self.get(self.variables[0])

    def get_xlabel(self):
        return self.variables[0]

class tran_solution(solution, _mutable_data):
    """Transient results

    **Parameters:**

    circ : circuit instance
        the circuit instance of the simulated circuit.
    tstart : float
        the transient simulation start time.
    tstop : float
        the transient simulation stop time.
    op : op_solution instance
        the Operating Point (OP) used to start the transient analysis.
    method : str
        the differentiation method employed.
    outfile : str
        the filename of the save file.
        Use "stdout" to write to the standard output.
    """
    def __init__(self, circ, tstart, tstop, op, method, outfile):
        solution.__init__(self, circ, outfile)
        self.sol_type = "TRAN"
        self.start_op = op
        self.tstart, self.tstop = tstart, tstop
        self.method = method

        self._lock = False

        nv_1 = circ.get_nodes_number() - 1 # numero di soluzioni di tensione (al netto del ref)
        self.variables = ["T"]
        self.units.update({"T":"s"})

        for index in range(nv_1):
            varname = ("V%s" % (str(circ.nodes_dict[index + 1]),)).upper()
            self.variables += [varname]
            self.units.update({varname:"V"})
            if circ.is_int_node_internal_only(index+1):
                self.skip_nodes_list.append(index)

        for elem in circ:
            if circuit.is_elem_voltage_defined(elem):
                varname = ("I(%s)" % (elem.part_id.upper(),)).upper()
                self.variables += [varname]
                self.units.update({varname:"A"})

    def __str__(self):
        return ("<TRAN simulation results for '%s' (netlist %s), from %g s to" +
                " %g s. Diff. method %s. Run on %s, data file %s>") % \
               (self.netlist_title, self.netlist_file, self.tstart, self.tstop,
                self.method, self.timestamp, self.filename)

    def add_line(self, time, x):
        """This method adds a solution and its corresponding time value to the results set.
        """
        if not self._lock:
            time = np.array([[time]])
            data = np.concatenate((time, x), axis=0)
            self._add_data(data)
        else:
            raise RuntimeError("Attempting to add values to a complete " +
                               "result set.")

    def lock(self):
        self._lock = True

    def get_x(self):
        return self.get(self.variables[0])

    def get_xlabel(self):
        return self.variables[0]




class case_insensitive_dict(object):
    """A dictionary that uses case-insensitive strings as keys.
    """
    def __init__(self):
        self._dict = {}

    def __len__(self):
        """Get the number of elements in the set."""
        return len(self._dict)

    def __str__(self):
        rpr = "{"
        keys = list(self._dict.keys())
        for i in range(len(keys)):
            rpr += "%s: %s" % (keys[i], self._dict[keys[i]])
            if i < len(keys) - 1:
                rpr += ", "
            else:
                rpr += "}"
        return rpr

    def __getitem__(self, name):
        """Get a specific variable, as from a dictionary."""
        keys = list(self._dict.keys())
        try:
            i = [k.upper() for k in keys].index(str(name).upper())
        except ValueError:
            raise KeyError(name)
        return self._dict[keys[i]]

    def get(self, name, default=None):
        """Given the case-insensitive string key ``name``, return its corresponding value.

        If not found, return ``default``.
        """
        try:
            keys = list(self._dict.keys())
            i = [k.upper() for k in keys].index(name.upper())
        except ValueError:
            return default
        return self._dict[keys[i]]

    def has_key(self, name):
        """Determine whether the result set contains the variable ``name``."""
        return name.upper() in [k.upper() for k in list(self._dict.keys())]

    def __contains__(self, name):
        """Determine whether the result set contains a variable."""
        return name.upper() in [k.upper() for k in list(self._dict.keys())]

    def keys(self):
        """Get all keys"""
        return list(self._dict.keys())

    def values(self):
        """Get all values"""
        return list(self._dict.values())

    def items(self):
        """Get all keys and values pairs"""
        return list(self._dict.items())

    def update(self, adict):
        """Update the dictionary contents with the mapping in the dictionary ``adict``.
        """
        return self._dict.update(adict)

    # iterator methods
    def __iter__(self):
        """Iterator"""
        return self._dict.__iter__()
