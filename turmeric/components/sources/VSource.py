from ..VoltageDefinedComponent import VoltageDefinedComponent
from ..tokens import rex, Value, Label, Node, EqualsParam, ParamDict
import logging
import numpy as np

class VSource(VoltageDefinedComponent):
    """An ideal voltage source.

    .. image:: images/elem/vsource.svg

    Defaults to a DC voltage source.

    To implement a time-varying source:

    * set ``_time_function`` to an appropriate instance having a
      ``value(self, time)`` method,
    * set ``is_timedependent`` to ``True``.

    **Parameters:**

    part_id : string
        The unique identifier of this element. The first letter should be
        ``'V'``.
    n1 : int
        *Internal* node to be connected to the anode.
    n2 : int
        *Internal* node to be connected to the cathode.
    dc_value : float
        DC voltage in Volt.
    ac_value : complex float, optional
        AC voltage in Volt. Defaults to no AC characteristics,
        ie :math:`V(\\omega) = 0 \\;\\;\\forall \\omega > 0`.

    """

    def __init__(self, part_id, n1, n2, dc_value, ac_value=0):
        super().__init__(part_id, n1, n2, dc_value)
        self.abs_ac = np.abs(ac_value) if ac_value else None
        self.arg_ac = np.angle(ac_value) if ac_value else None
        self.is_nonlinear = False
        self.is_symbolic = True
        self.is_timedependent = False
        self._time_function = None
        if dc_value is not None:
            self.dc_guess = [self.value]

    @classmethod
    def from_line(cls, line, circ):
        """
        Format: v<label> n1 n2 [type=vdc vdc=float] [type=vac vac=float] [type=....]
        Example: v1 1 0 type=vdc vdc=5
        """
        import re
        types = {'vdc':0,'vac':0,'pulse':7,'exp':6,'sin':5,'sffm':5,'am':5}
        net_objs = [Label,Node,Node,ParamDict]
        r = "^" + "v" + '(?: +)'.join([rex(o) for o in net_objs])
        match = re.search(r,line.strip().lower())

        try:
            tokens = [n(g) for n,g in zip(net_objs,match.groups())]
        except AttributeError as e:
            logging.exception(f"Failed to parse element from line\n\t`{line}'\n\tusing the regex `{r}'")

        params = tokens[3].value
        try:
            param_number = types[params['type']]
        except AttributeError as e:
            logging.exception(f"Type of source not specified in `{line}'")

        dc_value = float(params['vdc']) if 'vdc' in params else None
        vac = float(params['vac']) if 'vac' in params else None
        # FIXME: process type's time function properly
        function = None

        if dc_value == None and function == None:
            raise ValueError(f"Neither dc value nor time function defined for voltage source in:\n\t{line}")

        n1 = circ.add_node(str(tokens[1]))
        n2 = circ.add_node(str(tokens[2]))

        comp = cls(part_id=str(tokens[0]), n1=n1, n2=n2, dc_value=dc_value, ac_value=vac)

        if function is not None:
            comp.is_timedependent = True
            comp._time_function = function

        return [comp]

    def stamp(self, M, ZDC, ZAC, D):
        ZDC[index, 0] = -1.0 * self.V()

    def V(self, time=None):
        """Evaluate the voltage applied by the voltage source.

        If ``time`` is not supplied, or if it is set to ``None``, or if the
        source is only specified for DC, returns ``dc_value``.

        **Parameters:**

        time : float or None, optional
            The time at which the voltage is evaluated, if any.

        **Returns:**

        V : float
            The voltage, in Volt.
        """

        if (not self.is_timedependent or\
            self._time_function is None) or \
                (time is None and self.value is not None):
            return self.value
        else:
            return self._time_function(time)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        rep = f"{self.part_id} {self.n1} {self.n2} "
        rep += f"type=vdc vdc={self.value} " if self.value is not None else ''
        # TODO: netlist_parser not working with `arg=' from `self.arg_ac'
        rep += f"vac={str(self.abs_ac)} " if self.abs_ac is not None else ''
        rep += f"{self._time_function}" if self.is_timedependent else '' 
        return rep


    def get_op_info(self, ports_v, current):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the source terminals.
        current : float
            The current flowing in the voltage source, positive currents flow in
            ``n1`` and out of ``n2``.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v[0][0])
        power = self.V() * current
        op_keys = ['Part ID', "V(n1,n2) [V]", "I(n1->n2) [A]", "P [W]"]
        op_info = [self.part_id.upper(), self.V(), current, power]
        return op_keys, op_info

