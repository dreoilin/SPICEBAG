import numpy as np

from .. import settings
from .. import units

from .Component import Component
from .tokens import Label,Node,Model,ParamDict

DEFAULT_AREA = 1.0
DEFAULT_TEMP = 26.85
DEFAULT_T    = units.Kelvin(celsius=DEFAULT_TEMP)

class D(Component):
    """
    This component class describes the behaviour of a diode element in a circuit.
    
    The two important methods are:
        
        1. The istamp: This generates an effective current contribution of the
        companion model
        2. The g-stamp: computes the stamp for the differential cross-conductance
        of the e
    """
    
    def __init__(self, line, circ, models):
        self.net_objs = [Label,Node,Node,Model.defined(models),ParamDict.allowed_params(self,{
            'AREA' : { 'type' : float, 'default' : DEFAULT_AREA },
            'T'    : { 'type' : float, 'default' : DEFAULT_T    }
            },optional=True)]
        super().__init__(line)
        self.part_id = str(self.tokens[0])
        self.n1 = circ.add_node(str(self.tokens[1]))
        self.n2 = circ.add_node(str(self.tokens[2]))

        self.model = self.tokens[3].value

        self.is_nonlinear = True
        self.ports = ((self.n1, self.n2),)

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        pass

    def set_temperature(self, T):
        self.T = T

    def __repr__(self):
        """
        D<label> n1 n2 <model_id> [<AREA=value> <T=value>]
        """
        r = f"D{self.part_id} {self.n1} {self.n2} {self.model.model_id} "
        r += ' '.join([f'{p}={getattr(self,p)}' for p in ['AREA','T']])
        return r


    def get_output_ports(self):
        return self.ports

    def get_drive_ports(self, port):
        if port != 0:
            raise ValueError('Port {op} does not exist on D {self.part_id}')
        return self.ports

    def istamp(self, ports_v, time=0, reduced=True):
        """
        Generates the current stamp for the N matrix

        Parameters
        ----------
        ports_v : device ports
        time : dummy
        reduced : reduced matrix optional
             The default is True.

        Returns
        -------
        indices : position of stamps
        istamp : value of stamps

        """
        v = ports_v[0]
        i = self.model.get_i(v, self)
        istamp = np.array((i, -i), dtype=np.float64)
        indices = ((self.n1 - 1*reduced, self.n2 - 1*reduced), (0, 0))
        if reduced:
            delete_i = [pos for pos, ix in enumerate(indices[0]) if ix == -1]
            istamp = np.delete(istamp, delete_i, axis=0)
            indices = tuple(zip(*[(ix, j) for ix, j in zip(*indices) if ix != -1]))
        return indices, istamp

    def i(self, op_index, ports_v, time=0):  # with gmin added
        """
        Getter method to retrieve the diode current
        
        Time is a dummy variable
        """
        v = ports_v[0]
        i = self.model.get_i(v, self)
        return i

    def gstamp(self, ports_v, time=0, reduced=True):
        """
        Generates the transconductance stamp for the diode. The transconductance
        is generated by the diode model. This method returns the indices at which
        the diode stamps the J matrix and the value of the stamp

        Parameters
        ----------
        ports_v : device ports
        time : dummy argument
        reduced : TYPE, optional
             The default is True.

        Returns
        -------
        indices : positions of stamps
        stamp : value of gstamps

        """
        indices = ([self.n1 - 1]*2 + [self.n2 - 1]*2,
                   [self.n1 - 1, self.n2 - 1]*2)
        gm = self.model.get_gm(0, ports_v, 0, self)
        if gm == 0:
            gm = settings.gmin*2
        stamp = np.array(((gm, -gm),
                          (-gm, gm)), dtype=np.float64)
        if reduced:
            zap_rc = [pos for pos, i in enumerate(indices[1][:2]) if i == -1]
            stamp = np.delete(stamp, zap_rc, axis=0)
            stamp = np.delete(stamp, zap_rc, axis=1)
            indices = tuple(zip(*[(i, y) for i, y in zip(*indices) if (i != -1 and y != -1)]))
            stamp_flat = stamp.reshape(-1)
            stamp_folded = []
            indices_folded = []
            for ix, it in enumerate([(i, y) for i, y in zip(*indices)]):
                if it not in indices_folded:
                    indices_folded.append(it)
                    stamp_folded.append(stamp_flat[ix])
                else:
                    w = indices_folded.index(it)
                    stamp_folded[w] += stamp_flat[ix]
            indices = tuple(zip(*indices_folded))
            stamp = np.array(stamp_folded)
        return indices, stamp

    def g(self, op_index, ports_v, port_index, time=0):
        if not port_index == 0:
            raise Exception("Attepted to evaluate a D's gm on an unknown port.")
        gm = self.model.get_gm(self.model, op_index, ports_v, port_index, self)
        return gm
