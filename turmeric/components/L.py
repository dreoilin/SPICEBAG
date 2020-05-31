from .VoltageDefinedComponent import VoltageDefinedComponent
from .tokens import rex, Value, Label, Node

class L(VoltageDefinedComponent):
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,Value]
        super().__init__(line)

        self.part_id = str(self.tokens[0])
        self.n1 = circ.add_node(str(self.tokens[1]))
        self.n2 = circ.add_node(str(self.tokens[2]))
        self.value = float(self.tokens[3])
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0, time)
        D0[-1, -1] = -1 * self.value
        return (M0, ZDC0, ZAC0, D0, ZT0)

    def __repr__(self):
        """
        L<string> n1 n2 <value>
        """
        return f"L{self.part_id} {self.n1} {self.n2} {self.value}"
