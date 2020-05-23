#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian


"""

import math
import numpy as np
import sys

from . import components
from . import diode, mosq

from . import printing
from . import utilities

class Circuit(list):
    """The circuit class.

    **Parameters:**

    title : string
        The circuit title.

    filename : string, optional

        .. deprecated:: 0.09

        If the circuit instance corresponds to a netlist file on disk,
        set this to the netlist filename.

    """
    def __init__(self, title, filename=None):
        self.title = title
        self.filename = filename
        self.nodes_dict = {}  # {int_node:ext_node, int_node:ext_node}
        self.internal_nodes = 0
        self.models = {}
        self.gnd = '0'

    def __str__(self):
        s = "* " + self.title + "\n"
        for elem in self:
            s += elem.get_netlist_elem_line(self.nodes_dict) + "\n"
        return s[:-1]

    def create_node(self, name):
        """Creates a new circuit node

        If there is a node in the circuit with the same name, ValueError is
        raised.

        **Parameters:**

        name : string
            the _unique_ identifier of the node.

        **Returns:**

        node : string
            the _unique_ identifier of the node, to be used for subsequent
            element declarations, for example.

        :raises ValueError: if a new node with the given id cannot be created,
          for example because a node with the same name already exists in the
          circuit. The only exception is the ground node, which has the
          reserved id ``'0'``, and for which this method won't raise any
          exception.
        :raises TypeError: if the parameter ``name`` is not of "text" type
        """
        if not isinstance(name,str):
            raise TypeError("The node %s should have been of text type" % name)
        got_ref = 0 in self.nodes_dict
        if name not in self.nodes_dict:
            if name == '0':
                int_node = 0
            else:
                int_node = int(len(self.nodes_dict)/2) + 1*(not got_ref)
            self.nodes_dict.update({int_node:name})
            self.nodes_dict.update({name:int_node})
        else:
            raise ValueError('Impossible to create new node %s: node exists!' % name)
        return name

    def add_node(self, ext_name):
        
        # must be text (str unicode...)
        if not isinstance(ext_name, str):
            raise TypeError("The node %s should have been of text type" % ext_name)
        # test: do we already have it in the dictionary?
        if ext_name not in self.nodes_dict:
            if ext_name == '0':
                int_node = 0
            else:
                got_ref = 0 in self.nodes_dict
                int_node = int(len(self.nodes_dict)/2) + 1*(not got_ref)
            self.nodes_dict.update({int_node:ext_name})
            self.nodes_dict.update({ext_name:int_node})
        else:
            int_node = self.nodes_dict[ext_name]
        return int_node

    def get_nodes_number(self):
        """Returns the number of nodes in the circuit"""
        return int(len(self.nodes_dict)/2)


    def is_nonlinear(self):
        
        for elem in self:
            if elem.is_nonlinear:
                return True
        return False

    def get_locked_nodes(self):
        """Get all nodes connected to non-linear elements.

        This list is meant to be passed to ``dc_solve`` or ``mdn_solver`` to be
        used in ``get_td`` to evaluate the damping coefficient in a
        Newton-Rhapson iteration.

        **Returns:**

        locked_nodes : list
            A list of internal nodes.
        """
        locked_nodes = []
        nl_elements = [elem for elem in self if elem.is_nonlinear]
        for elem in nl_elements:
            oports = elem.get_output_ports()
            for index in range(len(oports)):
                ports = elem.get_drive_ports(index)
                for port in ports:
                    locked_nodes.append(port)
        return locked_nodes

    def ext_node_to_int(self, ext_node):
        
        return self.nodes_dict[ext_node]

    def int_node_to_ext(self, int_node):
        
        return self.nodes_dict[int_node]

    def has_duplicate_elem(self):
        
        all_ids = tuple(map(lambda e: e.part_id, self))
        return len(set(all_ids)) != len(all_ids)

    def get_ground_node(self):
        return '0'

    def get_elem_by_name(self, part_id):
        
        for e in self:
            if e.part_id.lower() == part_id.lower():
                return e
        raise ValueError('Element %s not found' % part_id)

    def add_model(self, model_type, model_label, model_parameters):

        if 'name' not in model_parameters:
            model_parameters.update({'name':model_label})
        elif model_type == "mosq":
            model_iter = mosq.mosq_mos_model(**model_parameters)
            model_iter.name = model_label
        elif model_type == "diode":
            model_iter = diode.diode_model(**model_parameters)
            model_iter.name = model_label
        else:
            raise CircuitError("Unknown model type %s" % (model_type,))
        self.models.update({model_label: model_iter})

    def remove_model(self, model_label):
        
        if self.models is not None and model_label in self.models:
            del self.models[model_label]
        # should print a warning here

    # TODO: refactor component addition into component classes
    # ADDING COMPONENTS
    def add_resistor(self, part_id, n1, n2, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        if value == 0:
            raise CircuitError("ZERO-valued resistors are not allowed.")

        elem = components.Resistor(part_id=part_id, n1=n1, n2=n2, value=value)
        self.append(elem)

    def add_capacitor(self, part_id, n1, n2, value, ic=None):
        
        if value == 0:
            raise CircuitError("ZERO-valued capacitors are not allowed.")

        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.Capacitor(part_id=part_id, n1=n1, n2=n2, value=value, ic=ic)

        self.append(elem)

    def add_inductor(self, part_id, n1, n2, value, ic=None):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.Inductor(part_id=part_id, n1=n1, n2=n2, value=value, ic=ic)

        self.append(elem)

    def add_vsource(self, part_id, n1, n2, dc_value, ac_value=0, function=None):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.sources.VSource(part_id=part_id, n1=n1, n2=n2, dc_value=dc_value,
                               ac_value=ac_value)

        if function is not None:
            elem.is_timedependent = True
            elem._time_function = function

        self.append(elem)

    def add_isource(self, part_id, n1, n2, dc_value, ac_value=0, function=None):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.sources.ISource(part_id=part_id, n1=n1, n2=n2, dc_value=dc_value,
                               ac_value=ac_value)

        if function is not None:
            elem.is_timedependent = True
            elem._time_function = function

        self.append(elem)

    def add_diode(self, part_id, n1, n2, model_label, models=None, Area=None,
                  T=None, ic=None, off=False):
        """Adds a diode to the circuit (also takes care that the nodes
        are added as well).

        **Parameters:**

        part_id : string
            The diode ID (eg "D1"). The first letter is always D.
        n1, n2 : string
            the nodes to which the element is connected. eg. ``"in"`` or
            ``"out_a"``
        model_label : string
            The diode model identifier. The model needs to be added
            first, then the elements using it.
        models : dict, optional
            List of available model instances. If not set or ``None``,
            the circuit models will be used (recommended).
        Area : float, optional
            Scaled device area (optional, defaults to 1.0)
        T : float, optional
            Operating temperature (no temperature dependence yet)
        ic : float, optional
            Initial condition (not really implemented yet)
        off : bool, optional
            Consider the diode to be initially off.
        """
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        if models is None:
            models = self.models
        if model_label not in models:
            raise ModelError("Unknown diode model id: " + model_label)

        elem = diode.diode(part_id=part_id, n1=n1, n2=n2, model=models[
                           model_label], AREA=Area, T=T, ic=ic, off=off)
        self.append(elem)


    def add_mos(self, part_id, nd, ng, ns, nb, w, l, model_label, models=None,
                m=1, n=1):
        """Adds a mosfet to the circuit (also takes care that the nodes
        are added as well).

        **Parameters:**

        part_id : string
            The mos part_id (eg "M1"). The first letter is always M.
        nd : string
            The drain node.
        ng : string
            The gate node.
        ns : string
            The source node.
        nb : string
            The bulk node.
        w : float
            The gate width.
        l : float
            The gate length.
        model_label : string
            The model identifier.
        models : dict, optional
            The circuit models.
        m : int, optional
            Shunt multiplier value. Defaults to 1.
        n : int, optional
            Series multiplier value, not always supported. Defaults to 1.
        """
        nd = self.add_node(nd)
        ng = self.add_node(ng)
        ns = self.add_node(ns)
        nb = self.add_node(nb)

        if models is None:
            models = self.models

        if model_label not in models:
            raise ModelError("Unknown model id: " + model_label)

        if isinstance(models[model_label], mosq.mosq_mos_model):
            elem = mosq.mosq_device(part_id, nd, ng, ns, nb, w, l,
                                    models[model_label], m, n)
        else:
            raise Exception("Unknown model type for " + model_label)

        self.append(elem)


    def add_cccs(self, part_id, n1, n2, source_id, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        elem = components.sources.FISource(part_id=part_id, n1=n1, n2=n2,
                                source_id=source_id, value=value)
        self.append(elem)

    def add_ccvs(self, part_id, n1, n2, source_id, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        elem = components.sources.HVSource(part_id=part_id, n1=n1, n2=n2,
                                source_id=source_id, value=value)
        
        self.append(elem)

    def add_vcvs(self, part_id, n1, n2, sn1, sn2, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        sn1 = self.add_node(sn1)
        sn2 = self.add_node(sn2)

        elem = components.sources.EVSource(part_id=part_id, n1=n1, n2=n2, sn1=sn1, sn2=sn2,
                                value=value)

        self.append(elem)


    def add_vccs(self, part_id, n1, n2, sn1, sn2, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        sn1 = self.add_node(sn1)
        sn2 = self.add_node(sn2)

        elem = components.sources.GISource(part_id=part_id, n1=n1, n2=n2, sn1=sn1, sn2=sn2,
                                value=value)

        self.append(elem)
    # END OF ADDING COMPONENTS


    def find_vde_index(self, elem_or_id, verbose=3):
        
        if not isinstance(elem_or_id, str):
            part_id = elem_or_id.part_id
        else:
            part_id = elem_or_id
        vde_index = 0
        for elem in self:
            if is_elem_voltage_defined(elem):
                if elem.part_id.upper() == part_id.upper():
                    break
                else:
                    vde_index += 1
        else:
            raise ValueError(("find_vde_index(): element %s was not found." +\
                              " This is a bug.") % (part_id,))
        printing.print_info_line(("%s found at index %d" % (part_id,
                                                            vde_index), 6),
                                 verbose)
        return vde_index

    def find_vde(self, index):
        
        index = index - len(self.nodes_dict)/2 + 1
        ni = 0
        for e in self:
            if is_elem_voltage_defined(e):
                if index == ni:
                    break
                else:
                    ni = ni + 1
        else: #executed if no break occurred
            raise IndexError('No element corresponds to vde index %d' %
                             (index + len(self.nodes_dict)/2 - 1))
        return e
    
    # TODO: refactor generation of M0 and ZDC0 into components' classes
    def generate_M0_and_ZDC0(self):
        n_of_nodes = self.get_nodes_number()
        M0 = np.zeros((n_of_nodes, n_of_nodes))
        ZDC0 = np.zeros((n_of_nodes, 1))

        # First, current defined, linear elements
        # == CD = {R , C , GISource, ISource (time independant)}
        
        # Next, voltage defined elements
        # == VD = { V (time independant ) , EVSource , HVSource , Inductor }
        # Operations common to all VD elements:
        #index = M0.shape[0]  # get_matrix_size(M0)[0]
        #M0 = utilities.expand_matrix(M0, add_a_row=True, add_a_col=True)
        #ZDC0 = utilities.expand_matrix(ZDC0, add_a_row=True, add_a_col=False)
        ## KCL
        #M0[elem.n1, index] = 1.0
        #M0[elem.n2, index] = -1.0
        ## KVL
        #M0[index, elem.n1] = +1.0
        #M0[index, elem.n2] = -1.0
        # Finally FISource

        for elem in self:
            if elem.is_nonlinear:
                continue
            elif isinstance(elem, components.Resistor):
                M0[elem.n1, elem.n1] = M0[elem.n1, elem.n1] + elem.g
                M0[elem.n1, elem.n2] = M0[elem.n1, elem.n2] - elem.g
                M0[elem.n2, elem.n1] = M0[elem.n2, elem.n1] - elem.g
                M0[elem.n2, elem.n2] = M0[elem.n2, elem.n2] + elem.g
            elif isinstance(elem, components.Capacitor):
                pass  # In a capacitor I(V) = 0
            elif isinstance(elem, components.sources.GISource):
                M0[elem.n1, elem.sn1] = M0[elem.n1, elem.sn1] + elem.alpha
                M0[elem.n1, elem.sn2] = M0[elem.n1, elem.sn2] - elem.alpha
                M0[elem.n2, elem.sn1] = M0[elem.n2, elem.sn1] - elem.alpha
                M0[elem.n2, elem.sn2] = M0[elem.n2, elem.sn2] + elem.alpha
            elif isinstance(elem, components.sources.ISource):
                if not elem.is_timedependent:  # convenzione normale!
                    ZDC0[elem.n1, 0] = ZDC0[elem.n1, 0] + elem.I()
                    ZDC0[elem.n2, 0] = ZDC0[elem.n2, 0] - elem.I()
                else:
                    pass  # vengono aggiunti volta per volta
            elif is_elem_voltage_defined(elem):
                pass
                # we'll add its lines afterwards
            elif isinstance(elem, components.sources.FISource):
                # we add these last, they depend on voltage sources
                # to sense the current
                pass
            else:
                logging.WARNING(f"Unknown linear element found: `{elem}'")
        # Next, voltage defined elements
        # process vsources
        # i generatori di tensione non sono pilotabili in tensione: g e' infinita
        # for each vsource, introduce a new variable: the current flowing through it.
        # then we introduce a KVL equation to be able to solve the circuit

        for elem in self:
            if is_elem_voltage_defined(elem):
                index = M0.shape[0]  # get_matrix_size(M0)[0]
                M0 = utilities.expand_matrix(M0, add_a_row=True, add_a_col=True)
                ZDC0 = utilities.expand_matrix(ZDC0, add_a_row=True, add_a_col=False)
                # KCL
                M0[elem.n1, index] = 1.0
                M0[elem.n2, index] = -1.0
                # KVL
                M0[index, elem.n1] = +1.0
                M0[index, elem.n2] = -1.0
                if isinstance(elem, components.sources.VSource) and not elem.is_timedependent:
                    # corretto, se e' def una parte tempo-variabile ci pensa
                    # mdn_solver a scegliere quella giusta da usare.
                    ZDC0[index, 0] = -1.0 * elem.V()
                elif isinstance(elem, components.sources.VSource) and elem.is_timedependent:
                    pass  # taken care step by step
                elif isinstance(elem, components.sources.EVSource):
                    M0[index, elem.sn1] = -1.0 * elem.alpha
                    M0[index, elem.sn2] = +1.0 * elem.alpha
                elif isinstance(elem, components.Inductor):
                    # ZDC0[index,0] = 0 pass, it's already zero
                    pass
                elif isinstance(elem, components.sources.HVSource):
                    index_source = self.find_vde_index(elem.source_id)
                    M0[index, n_of_nodes+index_source] = 1.0 * elem.alpha
                else:
                    print("dc_analysis.py: BUG - found an unknown voltage_def elem.")
                    print(elem)
                    sys.exit(33)
    
        # iterate again for devices that depend on voltage-defined ones.
        # TODO: matrix stamping for FISource
        for elem in self:
            if isinstance(elem, components.sources.FISource):
                local_i_index = self.find_vde_index(elem.source_id, verbose=0)
                M0[elem.n1, n_of_nodes + local_i_index] = M0[elem.n1, n_of_nodes + local_i_index] + elem.alpha
                M0[elem.n2, n_of_nodes + local_i_index] = M0[elem.n2, n_of_nodes + local_i_index] - elem.alpha
    
        # Seems a good place to run some sanity check
        # for the time being we do not halt the execution
        # utilities.check_ground_paths(M0, circ, reduced_mna=False, verbose=verbose)
    
        # all done
        self.M0 = M0
        self.ZDC0 = ZDC0

        #import codecs, json
        #for mat, matname in zip([M0, ZDC0],['M0','ZDC0']):
        #    with open(f'tests/data/matrices/VRD.{matname}.json','w+') as f:
        #        json.dump(mat.tolist(), f, sort_keys=True)
        
    # TODO: move stamping of ZAC0 into components' constructors; creation could be difficult 
        # if you are clever you should be able to alter this function
        # to generate ZAC0 using existing stamps and then slice matrix at end
        # talk to me about this
        # this method is called thousands of times in transient. We might need a quicker solution
    def generate_ZAC(self, time=None):
        
        # index to count voltage defined elements
        v_index = 0
        ZAC_size = self.M0.shape[0]-1
        NNODES = self.get_nodes_number()
        # create empty array to store ZAC0
        ZAC = np.zeros((ZAC_size, 1))
        for elem in self:
            if (isinstance(elem, components.sources.VSource) or isinstance(elem, components.sources.ISource)) and elem.is_timedependent:
                if isinstance(elem, components.sources.VSource):
                    ZAC[NNODES - 1 + v_index, 0] = -1 * elem.V(time)
                elif isinstance(elem, components.sources.ISource):
                    if elem.n1:
                        ZAC[elem.n1 - 1, 0] += elem.I(time)
                    if elem.n2:
                        ZAC[elem.n2 - 1, 0] += - elem.I(time)
            if is_elem_voltage_defined(elem):
                v_index += 1
        # all done
        self.ZAC = ZAC

# STATIC METHODS
# this should definitely be a member variable
# a sytematic way of sorting member variables would be nice
# TODO: make member function of Circuit
def is_elem_voltage_defined(elem):
    
    if isinstance(elem, components.sources.VSource) or isinstance(elem, components.sources.EVSource) or \
        isinstance(elem, components.sources.HVSource) or isinstance(elem, components.Inductor) \
            or (hasattr(elem, "is_voltage_defined") and elem.is_voltage_defined):
        return True
    else:
        return False
    
    
class NodeNotFoundError(Exception):
    pass


class CircuitError(Exception):
    pass


class ModelError(Exception):
    pass
