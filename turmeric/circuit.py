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
from . import diode

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
            if hasattr(elem,'__str__'):
                s += str(elem)
            elif hasattr(elem,'__repr__'):
                s += repr(elem)
            else:
                s += elem.get_netlist_elem_line(self.nodes_dict) 
            s += '\n'
        return s[:-1]

    def __repr__(self):
        s = "* " + self.title + "\n"
        for elem in self:
            if hasattr(elem,'__repr__'):
                s += repr(elem)
            else:
                s += elem.get_netlist_elem_line(self.nodes_dict) + "\n"
            s += '\n'
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

        elem = components.R(part_id=part_id, n1=n1, n2=n2, value=value)
        self.append(elem)

    def add_capacitor(self, part_id, n1, n2, value, ic=None):
        
        if value == 0:
            raise CircuitError("ZERO-valued capacitors are not allowed.")

        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.C(part_id=part_id, n1=n1, n2=n2, value=value, ic=ic)

        self.append(elem)

    def add_inductor(self, part_id, n1, n2, value, ic=None):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.L(part_id=part_id, n1=n1, n2=n2, value=value, ic=ic)

        self.append(elem)

    def add_vsource(self, part_id, n1, n2, dc_value, ac_value=0, function=None):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)

        elem = components.sources.V(part_id=part_id, n1=n1, n2=n2, value=dc_value, ac_value=ac_value)

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


    def add_cccs(self, part_id, n1, n2, source_id, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        elem = components.sources.FISource(part_id=part_id, n1=n1, n2=n2,
                                source_id=source_id, value=value)
        self.append(elem)

    def add_ccvs(self, part_id, n1, n2, source_id, value):
        
        n1 = self.add_node(n1)
        n2 = self.add_node(n2)
        elem = components.sources.H(part_id=part_id, n1=n1, n2=n2,
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
    
    def gen_matrices(self, time=0):
        n = self.get_nodes_number()
        M0 = np.zeros((n,n))
        ZDC0 = np.zeros((n, 1))
        ZAC0 = np.zeros(ZDC0.shape)
        D0 = np.zeros(M0.shape)
        ZT0 = np.zeros(ZDC0.shape)

        # First, current defined, linear elements
        # == CD = {R , C , GISource, ISource (time independant)}
        CD = [components.R, components.C, components.sources.GISource, components.sources.ISource]
        [elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time) for elem in self if type(elem) in CD]
        VD = [components.sources.V,components.sources.EVSource,components.sources.H, components.L]
        for elem in self:
            if type(elem) in VD:
                (M0, ZDC0, ZAC0, D0, ZT0) = elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time)

        #mats = [M0, ZDC0, ZAC0, D0, ZT0]
        #for n, m in zip(['M0', 'ZDC0', 'ZAC0', 'D0', 'ZT0'],mats):
        #    print(f"{n}: {m}")

        self.M0   = M0
        self.ZDC0 = ZDC0
        self.ZAC0 = ZAC0
        self.D0   = D0
        self.ZT0  = ZT0 

    # TODO: refactor generation of M0 and ZDC0 into components' classes
    def generate_M0_and_ZDC0(self):
        n = self.get_nodes_number()
        M0 = np.zeros((n,n))
        ZDC0 = np.zeros((n, 1))
        ZAC0 = np.zeros(ZDC0.shape)
        D0 = np.zeros(M0.shape)
        ZT0 = np.zeros(ZDC0.shape)

        # First, current defined, linear elements
        # == CD = {R , C , GISource, ISource (time independant)}
        CD = [components.R, components.C, components.sources.GISource, components.sources.ISource]
        [elem.stamp(M0, ZDC0, ZAC0, D0, ZT0) for elem in self if type(elem) in CD]
        VD = [components.sources.V,components.sources.EVSource,components.sources.H, components.L]
        for elem in self:
            if type(elem) in VD:
                (M0, ZDC0, ZAC0, D0, ZT0) = elem.stamp(M0, ZDC0, ZAC0, D0, ZT0)

        mats = [M0, ZDC0, ZAC0, D0, ZT0]
        for n, m in zip(['M0', 'ZDC0', 'ZAC0', 'D0', 'ZT0'],mats):
            print(f"{n}: {m}")

        self.M0 = M0
        self.ZDC0 = ZDC0

        
        # Next, voltage defined elements
        # == VD = { V (time independant ) , EVSource , H , L }
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


    # generate unreduced dynamic matrix. Might be good to bundle 
    # this in with MNA gen and have a separate get function
    def generate_D0(self, shape):
    
        D0 = np.zeros(self.M0.shape[0])
        nv = self.get_nodes_number()
        i_eq = 0 #each time we find a vsource or vcvs or ccvs, we'll add one to this.
        for elem in self:
            if is_elem_voltage_defined(elem) and not isinstance(elem, components.L):
                i_eq = i_eq + 1
            elif isinstance(elem, components.C):
                n1 = elem.n1
                n2 = elem.n2
                D0[n1, n1] = D0[n1, n1] + elem.value
                D0[n1, n2] = D0[n1, n2] - elem.value
                D0[n2, n2] = D0[n2, n2] + elem.value
                D0[n2, n1] = D0[n2, n1] - elem.value
            elif isinstance(elem, components.L):
                D0[ nv + i_eq, nv + i_eq ] = -1 * elem.value
                
                # carry on as usual
                i_eq = i_eq + 1
    

        return D0    
    
    # TODO: move stamping of ZAC0 into components' constructors
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
            if (isinstance(elem, components.sources.V) or isinstance(elem, components.sources.ISource)) and elem.is_timedependent:
                if isinstance(elem, components.sources.V):
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
    
    if isinstance(elem, components.sources.V) or isinstance(elem, components.sources.EVSource) or \
        isinstance(elem, components.sources.H) or isinstance(elem, components.L) \
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
