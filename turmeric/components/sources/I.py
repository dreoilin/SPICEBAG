from ..CurrentDefinedComponent import CurrentDefinedComponent
from ..IndependentSource import IndependentSource
from ..tokens import rex, Value, Label, Node, ParamDict

class I(IndependentSource, CurrentDefinedComponent):
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,ParamDict]
        super().__init__(line, circ)

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        ZDC0[self.n1, 0] += self.dc_value if self.dc_value is not None else 0.
        ZDC0[self.n2, 0] -= self.dc_value if self.dc_value is not None else 0.
        ZAC0[self.n1, 0] += self.ac_value if self.ac_value is not None else 0.
        ZAC0[self.n2, 0] -= self.ac_value if self.ac_value is not None else 0.
        ZT0[self.n1, 0]  += self._time_function(time) if self.is_timedependent else 0.
        ZT0[self.n2, 0]  -= self._time_function(time) if self.is_timedependent else 0.

    def __repr__(self):
        rep = f"{self.name}{self.part_id} {self.n1} {self.n2} "
        rep += f"type=idc idc={self.dc_value} " if self.dc_value is not None else ''
        # TODO: netlist_parser not working with `arg=' from `self.arg_ac'
        rep += f"iac={repr(self.ac_value)} " if self.ac_value is not None else ''
        rep += f"{repr(self._time_function)}" if self.is_timedependent else '' 
        return rep
