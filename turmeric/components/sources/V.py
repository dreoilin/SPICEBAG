from ..VoltageDefinedComponent import VoltageDefinedComponent
from ..tokens import rex, Value, Label, Node, ParamDict
import logging
import numpy as np
from ... import utilities

class V(VoltageDefinedComponent):
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

    #def __init__(self, part_id, n1, n2, dc_value, ac_value=0):
    def __init__(self, line, circ):
        self.net_objs = [Label,Node,Node,ParamDict]
        super().__init__(line)

        # TODO: have/find one list of accepted methods
        types = {'vdc':0,'vac':0,'pulse':7,'exp':6,'sin':5,'sffm':5,'am':5}
        params = self.tokens[3].value
        try:
            param_number = types[params['type']]
        except AttributeError as e:
            logging.exception(f"Type of source not specified or source type is unsupported in `{line}'")

        dc_value = None
        ac_value = None
        if params['type'] == 'vdc':
            if 'vdc' in params:
                dc_value = float(params['vdc'])
            else:
                raise KeyError(f"When specifying a dc voltage source, specify its value (vdc=<value>) : `{line}'")
        elif params['type'] == 'vac':
            if 'vac' in params:
                ac_value = float(params['vac'])
            else:
                raise KeyError(f'When specifying an ac voltage source, specify its value (vac=<value>) : `{line}')

        # TODO: test that time function is being parsed correctly
        function = self.parse_time_function(params['type'],[str(k)+'='+str(v) for k,v in params.items()],"voltage") if not dc_value and not ac_value else None

        if dc_value == None and function == None:
            raise ValueError(f"Neither dc value nor time function defined for voltage source in:\n\t{line}")

        n1 = circ.add_node(str(self.tokens[1]))
        n2 = circ.add_node(str(self.tokens[2]))

        self.part_id=str(self.tokens[0])
        self.n1=n1
        self.n2=n2
        self.value=dc_value
        self.ac_value=ac_value

        #super().__init__(part_id, n1, n2, dc_value)
        self.abs_ac = np.abs(self.ac_value) if self.ac_value else None
        self.arg_ac = np.angle(self.ac_value) if self.ac_value else None
        self.is_nonlinear = False
        self.is_symbolic = True
        self.is_timedependent = function is not None
        self._time_function = function if function is not None else None
        if self.value is not None:
            self.dc_guess = [self.value]

    # FIXME: this does not belong here
    def parse_time_function(self, ftype, line_elements, stype):
        import copy
        from ...time_functions import time_fun_specs

        if not ftype in time_fun_specs:
            raise ValueError(f"Unknown time function: {ftype}")
        prot_params = list(copy.deepcopy(time_fun_specs[ftype]['tokens']))

        fun_params = {}
        for i in range(len(line_elements)):
            token = line_elements[i]
            if token[0] == "*":
                break
            if token.strip().count('=') == 1:
                (label, value) = token.split('=')
            else:
                label, value = None, token
            assigned = False
            for t in prot_params:
                if (label is None and t['pos'] == i) or label == t['label']:
                    fun_params.update({t['dest']: self.convert(value, t['type'])})
                    assigned = True
                    break
            if assigned:
                prot_params.pop(prot_params.index(t))
                continue
            elif label == 'type':
                continue
            else:
                raise ValueError("Unknown .%s parameter: pos %d (%s=)%s" % \
                                         (ftype.upper(), i, label, value))

        missing = []
        for t in prot_params:
            if t['needed']:
                missing.append(t['label'])
        if len(missing):
            raise NetlistParseError("%s: required parameters are missing: %s" % (ftype, " ".join(line_elements)))
        # load defaults for unsupplied parameters
        for t in prot_params:
            fun_params.update({t['dest']: t['default']})

        from ...time_functions import sin, pulse, exp, sffm, am
        time_functions = {}
        for i in sin, pulse, exp, sffm, am:
            time_functions.update({i.__name__:i})

        fun = time_functions[ftype](**fun_params)
        fun._type = "V" * (stype.lower() == "voltage") + "I" * (stype.lower() == "current")
        return fun

    # FIXME: this does not belong here
    def convert(self, astr, rtype, raise_exception=False):
        
        if rtype == float:
            try:
                ret = float(Value(astr))
            except ValueError as msg:
                if raise_exception:
                    raise ValueError(msg)
                else:
                    ret = astr
        elif rtype == str:
            ret = astr
        elif rtype == bool:
            ret = convert_boolean(astr)
        elif raise_exception:
            raise ValueError("Unknown type %s" % rtype)
        else:
            ret = astr
        return ret

    # FIXME: this does not belong here
    def convert_boolean(self, value):
        
        if value == 'no' or value == 'false' or value == '0' or value == 0:
            return_value = False
        elif value == 'yes' or value == 'true' or value == '1' or value == 1:
            return_value = True
        else:
            raise ValueError("invalid boolean: " + value)

        return return_value

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0)
        ZDC0[-1, 0] = -1.0 * self.value if self.value is not None else 0.
        ZAC0[-1, 0] = -1.0 * self.ac_value if self.ac_value is not None else 0.
        ZT0[-1, 0] = -1.0 * self._time_function(0) if self._time_function is not None else 0.
        return (M0, ZDC0, ZAC0, D0, ZT0) 

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

        if (not self.is_timedependent or self._time_function is None) or (time is None and self.value is not None):
            return self.value
        else:
            return self._time_function(time)

    def __repr__(self):
        rep = f"{self.name}{self.part_id} {self.n1} {self.n2} "
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

