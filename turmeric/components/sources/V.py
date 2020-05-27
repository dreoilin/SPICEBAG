from ..VoltageDefinedComponent import VoltageDefinedComponent
from ..IndependentSource import IndependentSource
from ..tokens import rex, Value, Label, Node, ParamDict
import logging

class V(IndependentSource, VoltageDefinedComponent):

    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,ParamDict]
        super().__init__(line, circ)

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0, time)
        ZDC0[-1, 0] = -1.0 * self.dc_value if self.dc_value is not None else 0.
        ZAC0[-1, 0] = -1.0 * self.ac_value if self.ac_value is not None else 0.
        ZT0[-1, 0] = -1.0 * self._time_function(time) if self._time_function is not None else 0.
        return (M0, ZDC0, ZAC0, D0, ZT0) 

    def __repr__(self):
        rep = f"{self.name}{self.part_id} {self.n1} {self.n2} "
        rep += f"type=vdc vdc={self.dc_value} " if self.dc_value is not None else ''
        # TODO: netlist_parser not working with complex ac values
        rep += f"vac={str(self.ac_value)} " if self.ac_value is not None else ''
        rep += f"{self._time_function}" if self.is_timedependent else '' 
        return rep
