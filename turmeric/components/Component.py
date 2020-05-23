# -*- coding: iso-8859-1 -*-

import numpy as np

class Component(object):

    """Base Component class.

    This component is not meant for direct use, rather all other (simple)
    components are a subclass of this element.

    """

    def __init__(self, part_id=None, n1=None, n2=None, is_nonlinear=False, is_symbolic=True, value=None):
        self.part_id = part_id
        self.n1 = n1
        self.n2 = n2
        self.value = value
        self.is_nonlinear = is_nonlinear
        self.is_symbolic = is_symbolic

    #   Used by `get_netlist_elem_line` for value
    def __str__(self):
        return str(self.value)

    #   must be called to define the element!
    def set_char(self, i_function=None, g_function=None):
        if i_function:
            self.i = i_function
        if g_function:
            self.g = g_function

    def g(self, v):
        return 1./self.value

    def i(self, v):
        return 0

    def get_netlist_elem_line(self, nodes_dict):
        """A netlist line that, parsed, evaluates to the same instance

        **Parameters:**

        nodes_dict : dict
            The nodes dictionary of the circuit, so that the method
            can convert its internal node IDs to the corresponding
            external ones.

        **Returns:**

        ntlst_line : string
            The netlist line.
        """
        return "%s %s %s %g" % (self.part_id, nodes_dict[self.n1],
                                nodes_dict[self.n2], self.value)
