import numpy as np
import logging

from . import components

class Circuit(list):
    """
    This class contains:
        - all of the network elements
        - whether or not the circuit is linear/nonlinear
        - a method to add a node
        - a method to generate the MNA matrices
        - the number of nodes
        - wether or not the circuit is linear
        - a list of nodes attached to non linear elements (locked nodes)
    """
    
    def __init__(self, title, filename=None):
        self.title = title
        self.filename = filename
        self.nodes_dict = {}
        self.models = {}
        self.gnd = '0'

    def __str__(self):
        s = "* " + self.title + "\n"
        for elem in self:
            if hasattr(elem,'__str__'):
                s += str(elem)
            else:
                s += repr(elem)
            s += '\n'
        return s[:-1]

    def __repr__(self):
        s = "* " + self.title + "\n"
        s += '\n'.join(repr(c) for c in self)
        return s


    def add_node(self, nodename):
        nodename = str(nodename)
        if nodename in self.nodes_dict:
            return self.nodes_dict[nodename]
        else:
            nodenum = 0 if nodename == self.gnd else self.nnodes + 1*(not (0 in self.nodes_dict))
            self.nodes_dict.update({nodename : nodenum })
            self.nodes_dict.update({nodenum  : nodename})
            return int_node

    @property
    def nnodes(self):
        """Returns the number of nodes in this circuit"""
        return int(len(self.nodes_dict)/2)


    @property
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

    def gen_matrices(self, time=0):
        """
        This method generates the MNA matrices for the circuit simulation
        These matrices include:
            
            M0 : The unreduced MNA matrix
            D0 : the unreduced Dynamic matrix
            ZDC0: unreduced DC contribution
            ZAC0: unreduced AC contribution
            ZT0: unreduced transient contribution
            
        Current defined elements stamp first. Voltage defined elements
        (which need KCL) stamp second.
        
        Parameters
        ----------
        time : used in ZT generation, optional

        """
        # First, current defined, linear elements
        # == CD = {R , C , G, I}
        # Next, voltage defined elements
        # == VD = { V , L }
    
        n = self.nnodes
        M0 = np.zeros((n,n))
        ZDC0 = np.zeros((n, 1))
        ZAC0 = np.zeros(ZDC0.shape)
        D0 = np.zeros(M0.shape)
        ZT0 = np.zeros(ZDC0.shape)
        # current defined elements
        CD = [components.R, components.C, components.sources.G, components.sources.I]
        [elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time) for elem in self if type(elem) in CD]
        VD = [components.sources.V, components.L]
        for elem in self:
            if type(elem) in VD:
                (M0, ZDC0, ZAC0, D0, ZT0) = elem.stamp(M0, ZDC0, ZAC0, D0, ZT0, time)

        self.M0   = M0
        self.ZDC0 = ZDC0
        self.ZAC0 = ZAC0
        self.D0   = D0
        self.ZT0  = ZT0
 
    def generate_J_and_N(self, J, N, x, time):
        
        """
        This method generates the Jacobian (the effective conductance contribution)
        and the N(x) (the effective current contribution) of non-linear circuit
        elements.
        
        """
        
        for elem in self:
            if elem.is_nonlinear:
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
                        N[iis] += i.reshape(-1)
                        continue
                    if n1 or n2:
                        iel = elem.i(index, v_dports, time)
                    if n1:
                        N[n1m1, 0] = N[n1m1, 0] + iel
                    if n2:
                        N[n2m1, 0] = N[n2m1, 0] - iel
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
            
        return J, N

