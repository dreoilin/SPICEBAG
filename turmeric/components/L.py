from .VoltageDefinedComponent import VoltageDefinedComponent
from .tokens import rex, Value, Label, Node

class L(VoltageDefinedComponent):
    """An inductor.

    .. image:: images/elem/inductor.svg

    **Parameters:**

    part_id : string
        The unique identifier of this element. The first letter should be
        ``'L'``.
    n1 : int
        *Internal* node to be connected to the anode.
    n2 : int
        *Internal* node to be connected to the cathode.
    value : float
        The inductance in Henry.
    """
    #
    #             L
    #  n1 o----((((((((----o n2
    #
    #
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,Value]
        super().__init__(line)

        self.part_id = str(self.tokens[0])
        self.n1 = circ.add_node(str(self.tokens[1]))
        self.n2 = circ.add_node(str(self.tokens[2]))
        self.value = float(self.tokens[3])
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        D0[-1, -1] *= -1 * elem.value

    def __repr__(self):
        """
        L<string> n1 n2 <value>
        """
        return f"L{self.part_id} {self.n1} {self.n2} {self.value}"

    def get_op_info(self, ports_v, current):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the inductor terminals.
        current : float
            The current flowing in the inductor, positive currents flow in ``n1``
            and out of ``n2``.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v[0][0])
        energy = .5 * self.value * current**2
        op_keys = ['Part ID', u"\u03d5(n1,n2) [Wb]", "I(n1->n2) [A]", "E [J]"]
        op_info = [self.part_id.upper(), self.value*current, current, energy]
        return op_keys, op_info
