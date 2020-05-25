from ..VoltageDefinedComponent import VoltageDefinedComponent
from ..tokens import rex, Value, Label, Node

class H(VoltageDefinedComponent):  # H

    """Linear current-controlled voltage source

    .. image:: images/elem/ccvs.svg

    The source port is an existing voltage source, used to sense the current
    controlling the voltage source connected to the destination port.

    Mathematically, it is equivalent to the following:

    .. math::

        \\left\\{
        \\begin{array}{ll}
            V(sn_1) - V(sn_2) = V_S \\\\
            Vn_1 - Vn_2 = \\alpha * I[V_s]
        \\end{array}
        \\right.

    Where :math:`I[V_s]` is the current flowing in the source port, :math:`V_s`
    is the voltage applied between the nodes :math:`sn_1` and :math:`sn_2`.
    The remaining symbols are explained in the Parameters section below.

    .. note::

        This simulator uses the passive convention: a positive current flows
        into the element through the anode and exits through the cathode.

    **Parameters:**

    n1 : int
        *Internal* node to be connected to the anode of the output port.
    n2 : int
        *Internal* node to be connected to the cathode of the output port.
    value : float
        Proportionality constant :math:`\\alpha` between the sense current and
        the output voltage, in V/A.
    source_id : string
        ``part_id`` of the current-sensing voltage source, eg. ``'V1'`` or
        ``'VSENSE'``.

    """

    def __init__(self, line, circ):
        'H<string> n1 n2 <label> <constant>'
        self.net_objs = [Label,Node,Node,Label,Value]
        super().__init__(line)
        self.part_id = str(self.tokens[0])
        self.n1 = circ.add_node(str(self.tokens[1]))
        self.n2 = circ.add_node(str(self.tokens[2]))
        controlling_label = str(self.tokens[3])
        self.alpha = float(self.tokens[4])
        self.is_nonlinear = False

        vde_index = 0
        for elem in [ e for e in circ if isinstance(self,VoltageDefinedComponent)]:
            if elem.part_id.upper() == controlling_label.upper():
                break
            else:
                vde_index += 1
        else:
            raise ValueError(f"Could not find source `{label}' specified before parsing CCVS `{self.part_id}'")
        self.source_id = vde_index # + circ.get_nodes_number() # TODO: Until this is correct, H not usable

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0)
        M0[-1, n_of_nodes+index_source] = 1.0 * elem.alpha
        return (M0, ZDC0, ZAC0, D0, ZT0) 

    def __repr__(self):
        """
        H<string> n1 n2 <label> <constant>
        """
        return f"H{self.part_id} {self.n1} {self.n2} {self.source_id} {self.alpha}"


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
        return "%s %s %s %s %g" % (self.part_id, nodes_dict[self.n1],
                                nodes_dict[self.n2], self.source_id,
                                self.alpha)

