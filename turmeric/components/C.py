from .CurrentDefinedComponent import CurrentDefinedComponent
from .tokens import rex, Value, Label, Node

class C(CurrentDefinedComponent):
    """A capacitor.

    .. image:: images/elem/capacitor.svg

    **Parameters:**

    part_id : string
        The unique identifier of this element. The first letter should be
        ``'C'``.
    n1 : int
        *Internal* node to be connected to the anode.
    n2 : int
        *Internal* node to be connected to the cathode.
    value : float
        The capacitance in Farads.
    """
    #
    #               |  |
    #               |  |
    #     n1 o------+  +-------o n2
    #               |  |
    #               |  |
    #
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,Value]
        super().__init__(line)

        self.value=float(self.tokens[3])
        if self.value == 0:
            raise ValueError(f"A capacitor must have a value: `{line}'")

        self.part_id=str(self.tokens[0])
        self.n1=circ.add_node(str(self.tokens[1]))
        self.n2=circ.add_node(str(self.tokens[2]))
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        D0[self.n1, self.n1] += self.value
        D0[self.n1, self.n2] -= self.value
        D0[self.n2, self.n2] += self.value
        D0[self.n2, self.n1] -= self.value


    def __repr__(self):
        """
        C<string> n1 n2 <value>
        """
        return f"C{self.part_id} {self.n1} {self.n2} {self.value}"

    def get_op_info(self, ports_v):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the capacitor terminals.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v[0][0])
        qn1n2 = float(ports_v[0][0] * self.value)
        energy = float(.5 * ports_v[0][0] ** 2 * self.value)
        op_keys = ['Part ID', "V(n1-n2) [V]", "Q [C]", "E [J]"]
        op_info = [self.part_id.upper(), vn1n2, qn1n2, energy]
        return op_keys, op_info
