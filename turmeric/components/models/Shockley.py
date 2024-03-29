from ... import units
from ...numerical import newtonRaphson
from ...memoized import memoized
import numpy as np
from ... import settings
from turmeric.components.models.Model import Model
from turmeric.components.tokens import NoLabel, Label, ParamDict, Value

Tref = 300


# DEFAULTS MUST BE SPECIFIED IN POSTFIX SI UNITS
DEFAULT_BV   = 'inf'
DEFAULT_EG   = 1.11 
DEFAULT_IBV  = '1m'
DEFAULT_IS   = '10f'
DEFAULT_ISR  = 0.0   
DEFAULT_N    = 1.0 
DEFAULT_NR   = 2.0 
DEFAULT_RS   = 0.0  
DEFAULT_TEMP = 26.85
DEFAULT_T    = units.Kelvin(celsius=DEFAULT_TEMP)


class Material:
    def __init__(self):
        pass;
    def Eg(self, T=DEFAULT_T):
        return (self.Eg_0 - self.alpha * T ** 2 / (self.beta + T))  # eV

    def ni(self, T=DEFAULT_T):
        return self.n_i_0 * (T / Tref)**(3/2) * np.exp(self.Eg(Tref) / (2 * units.Vth(Tref)) - self.Eg(T) / (2 * units.Vth(T)))

class silicon(Material):
    """
    
    A small class holding the material properties of silicon
    to model device temperature properties
    
    """
    def __init__(self):
        self.esi = 104.5 * 10 ** -12
        self.eox = 34.5 * 10 ** -12  
        self.Eg_0=1.16
        self.alpha=0.000702
        self.beta=1108
        self.n_i_0=1.45 * 10 ** 16

si = silicon()

class Shockley(Model):
    def __init__(self, line):
        self.net_objs = [Label,Label,ParamDict.allowed_params(self,{
            'BV'   : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_BV  )},
            'EG'   : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_EG  )},
            'IBV'  : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_IBV )},
            'IS'   : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_IS  )},
            'ISR'  : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_ISR )},
            'N'    : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_N   )},
            'NR'   : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_NR  )},
            'RS'   : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_RS  )},
            'TEMP' : { 'type' : lambda v: float(Value(v)) , 'default' : str(DEFAULT_TEMP)},
            },optional=True)]
        super().__init__(line)
        self.model_id = str(self.tokens[2])
        self.T    = DEFAULT_T
        self.last_vd = None
        self.VT   = units.k * self.T / units.e
        self.material=si

    def __repr__(self):
        return f".model D {self.model_id} IS={self.IS} N={self.N} ISR={self.ISR}\
                NR={self.NR} RS={self.RS} BV={self.BV} IBV={self.IBV} TEMP={self.TEMP}\
                EG={self.EG}"    

    @memoized
    def get_i(self, vext, dev):
        """
        Calculates the device current using a newton raphson method
        for a given applied voltage vext
        returns:
            i : current
        """
        if dev.T != self.T:
            self.set_temperature(dev.T)
        if not self.RS:
            i = self._get_i(vext)
            dev.last_vd = vext
        else:
            vd = dev.last_vd if dev.last_vd is not None else 10*self.VT
            vd = newtonRaphson(self._obj_irs, vd, df=self._obj_irs_prime,
                    args=(vext, dev), tol=settings.vea, MAXITERS=500)
            i = self._get_i(vext-vd)
            dev.last_vd = vd
        return i

    def _obj_irs(self, x, vext, dev):
        """
        Internal function for newton raphson method
        """
        # obj fn for newton
        return x/self.RS-self._get_i(vext-x)

    def _obj_irs_prime(self, x, vext, dev):
        """
        Internal function for newton raphson method

        """
        # obj fn derivative for newton
        # first term
        ret = 1./self.RS
        # disable RS
        RSSAVE = self.RS
        self.RS = 0
        # second term
        ret += self.get_gm(0, (vext-x,), 0, dev)
        # renable RS
        self.RS = RSSAVE
        return ret

    @memoized
    def _safe_exp(self, x):
        return np.exp(x) if x < 70 else np.exp(70) + 10 * x

    def _get_i(self, v):
        """
        Getter function for diode current
        We model:
            forward effect
            recombination effect
            reverse effect

        """
        # forward
        i_fwd= self.IS * (self._safe_exp(v/(self.N * self.VT)) - 1)
        # recombination
        i_rec= self.ISR* (self._safe_exp(v/(self.NR * self.VT)) - 1)
        # reverse saturation
        i_rev=-self.IS * (self._safe_exp(-(v+self.BV)/(self.VT)) - 1)

        return i_fwd+i_rec+i_rev

    @memoized
    def get_gm(self, op_index, ports_v, port_index, dev):
        """
        Provides the device transconductance. Computed in two separate
        ways depending on whether contact resistance is modelled.

        Returns
        -------
        gm : device transconductance

        """
        if dev.T != self.T:
            self.set_temperature(dev.T)
        v=ports_v[0]
        # derivative wrt V
        gm = self.IS / (self.N * self.VT) *\
                self._safe_exp(v / (self.N * self.VT)) +\
                -self.IS/self.VT * (self._safe_exp(-(v+self.BV)/self.VT)) +\
                self.ISR / (self.NR * self.VT) *\
                self._safe_exp(v / (self.NR * self.VT))

        if self.RS != 0.0:
            gm = 1. / (self.RS + 1. / (gm + 1e-3*settings.gmin))
        return gm

    def set_temperature(self, T):
        """
        Sets the diode temperature adn alters the physical properties
        accordingly

        Parameters
        ----------
        T : temp

        """
        # alter properties based on T
        T = float(T)
        self.EG = self.material.Eg(T) if self.material!=None else self.EG
        self.IS = self.IS*(T/self.T)**(self.XTI/self.N)*np.exp(-units.e*(self.material.Eg(units.Tref) if self.material!=None else self.EG)/(self.N*units.k*T)*(1 - T/self.T))
        self.BV = self.BV - self.TBV*(T - self.T)
        self.RS = self.RS*(1 + self.TRS*(T - self.T))
        self.T = T




