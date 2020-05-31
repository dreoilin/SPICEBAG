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
        rep = f"R{self.part_id} {self.n1} {self.n2} {self.value}"
        return rep

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        M0[self.n1, self.n1] += 1./self.value
        M0[self.n1, self.n2] -= 1./self.value
        M0[self.n2, self.n1] -= 1./self.value
        M0[self.n2, self.n2] += 1./self.value
