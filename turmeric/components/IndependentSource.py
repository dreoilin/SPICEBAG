from .Component import Component
import numpy as np
from ..TVSourceFunctions import tvsourcefunctions, SIN

class IndependentSource(Component):
    def __init__(self, line, circ):
        super().__init__(line)

        params = self.tokens[3].value
        try:
            params['type']
        except AttributeError as e:
            logging.exception(f"Type of source not specified or source type is unsupported in `{line}'")

        dc_value = None
        ac_value = None
        if 'vdc' in params['type'] or 'idc' in params['type']:
            if 'vdc' in params:
                dc_value = float(params['vdc'])
            elif 'idc' in params:
                dc_value = float(params['idc'])
            else:
                raise KeyError(f"When specifying a dc independent source, specify its value ([vdc|idc]=<value>) : `{line}'")
        if 'vac' in params['type'] or 'iac' in params['type']:
            if 'vac' in params: # TODO: parse a complex number instead of a float
                ac_value = float(params['vac'])
            elif 'iac' in params:
                ac_value = float(params['iac'])
            else:
                raise KeyError(f'When specifying an ac independent source, specify its value ([vac|iac]=<value>) : `{line}')

        # TODO: test that time function is being parsed correctly
        timefn_type = None
        if isinstance(params['type'],list):
            non_acdc_types = [t for t in params['type'] if t != 'vac' and t != 'vdc' and t != 'iac' and t != 'idc']
            timefn_type = non_acdc_types[0] if len(non_acdc_types) >0 else None
        else:
            timefn_type = params['type'] if params['type'] not in ['vdc','vac','idc','iac'] else None
        # Get rid of parsed parameters
        for p in ['vdc','vac','idc','iac','type']:
            params.pop(p,None)
        function = tvsourcefunctions[timefn_type.lower()](params) if timefn_type is not None else None

        if dc_value == None and function == None:
            raise ValueError(f"Neither dc value nor time function defined for independent source in:\n\t{line}")

        self.part_id=str(self.tokens[0])
        self.n1 = circ.add_node(str(self.tokens[1]))
        self.n2 = circ.add_node(str(self.tokens[2]))
        self.dc_value=dc_value
        self.ac_value=ac_value

        self.is_nonlinear = False
        self.is_timedependent = function is not None
        self._time_function = function if function is not None else None
        if self.dc_value is not None:
            self.dc_guess = [self.dc_value]

