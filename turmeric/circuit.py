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
        self.nodes_dict = {}
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

    # TODO: change to property
    def get_nodes_number(self):
        """Returns the number of nodes in the circuit"""
        return int(len(self.nodes_dict)/2)


    # TODO: change to property
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

    # TODO: has_duplicate_elem only used in one place, put it there
    def has_duplicate_elem(self):
        
        all_ids = tuple(map(lambda e: e.part_id, self))
        return len(set(all_ids)) != len(all_ids)

    def find_vde_index(self, elem_or_id):
        
        if not isinstance(elem_or_id, str):
            part_id = elem_or_id.part_id
        else:
            part_id = elem_or_id
        vde_index = 0
        for elem in self:
            if isinstance(elem, components.VoltageDefinedComponent):
                if elem.part_id.upper() == part_id.upper():
                    break
                else:
                    vde_index += 1
        else:
            raise ValueError(("find_vde_index(): element %s was not found. This is a bug.") % (part_id,))
        printing.print_info_line(("%s found at index %d" % (part_id,vde_index), 6),0)
        return vde_index

    def gen_matrices(self, time=0):
        # First, current defined, linear elements
        # == CD = {R , C , G, I}
        # Next, voltage defined elements
        # == VD = { V , E , H , L }
        # Finally F
        n = self.get_nodes_number()
        M0 = np.zeros((n,n))
        ZDC0 = np.zeros((n, 1))
        ZAC0 = np.zeros(ZDC0.shape)
        D0 = np.zeros(M0.shape)
        ZT0 = np.zeros(ZDC0.shape)

        CD = [components.R, components.C, components.sources.G, components.sources.I]
        [elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time) for elem in self if type(elem) in CD]
        VD = [components.sources.V,components.sources.E,components.sources.H, components.L]
        for elem in self:
            if type(elem) in VD:
                (M0, ZDC0, ZAC0, D0, ZT0) = elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time)

        self.M0   = M0
        self.ZDC0 = ZDC0
        self.ZAC0 = ZAC0
        self.D0   = D0
        self.ZT0  = ZT0 


class NodeNotFoundError(Exception):
    pass


class CircuitError(Exception):
    pass


class ModelError(Exception):
    pass
