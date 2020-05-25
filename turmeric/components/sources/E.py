from ..VoltageDefinedComponent import VoltageDefinedComponent
class E(VoltageDefinedComponent):
    """
    VCVS
    """
    def __init__(self, part_id, n1, n2, value, sn1, sn2):
        self.net_objs = [Label,Node,Node,Node,Node,Value]
        self.part_id = str(self.tokens[0])
        self.n1  = str(self.tokens[1])
        self.n2  = str(self.tokens[2])
        self.sn1 = str(self.tokens[3])
        self.sn2 = str(self.tokens[4])
        self.alpha = float(self.tokens[5])
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0)
        M0[-1, elem.sn1] = -float(elem.alpha)
        M0[-1, elem.sn2] =  float(elem.alpha)
        return (M0, ZDC0, ZAC0, D0, ZT0) 

    def __repr__(self):
        """
        E<string> n+ n- ns+ ns- <value>
        """
        return f"E{self.part_id} {self.n1} {self.n2} {self.sn1} {self.sn2} {self.alpha}"

