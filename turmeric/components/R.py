from .CurrentDefinedComponent import CurrentDefinedComponent
from .tokens import rex, Value, Label, Node

class R(CurrentDefinedComponent):

    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,Value]
        super().__init__(line)

        self.value=float(self.tokens[3])
        if self.value == 0:
            raise ValueError(f"A resistor must have a value: `{line}'")

        self.part_id=str(self.tokens[0])
        self.n1=circ.add_node(str(self.tokens[1]))
        self.n2=circ.add_node(str(self.tokens[2]))
        self.is_nonlinear = False

    def __repr__(self):
        rep = f"{self.name}{self.part_id} {self.n1} {self.n2} {self.value}"
        return rep

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        M0[self.n1, self.n1] += 1./self.value
        M0[self.n1, self.n2] -= 1./self.value
        M0[self.n2, self.n1] -= 1./self.value
        M0[self.n2, self.n2] += 1./self.value

    def get_op_info(self, ports_v):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the resistor terminals.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v[0][0])
        in1n2 = float(ports_v[0][0]/self.value)
        power = float(ports_v[0][0] ** 2 / self.value)
        op_keys = ['Part ID', u"R [\u2126]", "V(n1,n2) [V]", "I(n1->n2) [A]", "P [W]"]
        op_info = [self.part_id.upper(), self.value, vn1n2, in1n2, power]
        return op_keys, op_info
