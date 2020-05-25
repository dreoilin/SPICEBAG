from ..CurrentDefinedComponent import CurrentDefinedComponent
from ..tokens import rex, Value, Label, Node

class G(CurrentDefinedComponent):
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,Value]
        super().__init__(line)
        self.part_id = str(self.tokens[0])
        self.n1  = str(self.tokens[1])
        self.n2  = str(self.tokens[2])
        self.sn1 = str(self.tokens[3])
        self.sn2 = str(self.tokens[4])
        self.alpha = float(self.tokens[5])
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        M0[self.n1, self.sn1] = M0[self.n1, self.sn1] + self.alpha
        M0[self.n1, self.sn2] = M0[self.n1, self.sn2] - self.alpha
        M0[self.n2, self.sn1] = M0[self.n2, self.sn1] - self.alpha
        M0[self.n2, self.sn2] = M0[self.n2, self.sn2] + self.alpha

    def __repr__(self):
        """
        G<string> n+ n- ns+ ns- <value>
        """
        return f"G{self.part_id} {self.n1} {self.n2} {self.sn1} {self.sn2} {self.alpha}"

