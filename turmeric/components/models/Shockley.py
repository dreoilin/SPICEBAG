from ... import units
from ...numerical import newtonRaphson
from ...memoized import memoized
import numpy as np
from ... import settings

Tref = 300

DEFAULT_BV   = float('inf')  
DEFAULT_EG   = 1.11 
DEFAULT_IBV  = 1e-3 
DEFAULT_IS   = 1e-14  
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
    def __init__(self):
        self.esi = 104.5 * 10 ** -12  # F/m
        self.eox = 34.5 * 10 ** -12  # F/m
        self.Eg_0=1.16
        self.alpha=0.000702
        self.beta=1108
        self.n_i_0=1.45 * 10 ** 16

#: Silicon class instantiated.
si = silicon()

class Shockley(object):
    def __init__(self, name, BV=None, EG=None, IBV=None, IS=None, ISR=None, N=None, NR=None, RS=None, TEMP=None, material=si):
        self.name = name
        self.BV   = float(BV) if BV is not None else DEFAULT_BV
        self.EG   = float(EG) if EG is not None else DEFAULT_EG
        self.IBV  = float(IBV) if IBV is not None else DEFAULT_IBV
        self.IS   = float(IS) if IS is not None else DEFAULT_IS
        self.ISR  = float(ISR) if ISR is not None else DEFAULT_ISR
        self.N    = float(N) if N is not None else DEFAULT_N
        self.NR   = float(NR) if NR is not None else DEFAULT_NR
        self.RS   = float(RS) if RS is not None else DEFAULT_RS
        self.TEMP = float(TEMP) + units.ZERO_CELSIUS if TEMP is not None else DEFAULT_TEMP
        self.T    = DEFAULT_T
        self.last_vd = None
        self.VT   = units.k * self.T / units.e
        self.material=material
        
    def __repr__(self):
        return f".model D {self.name} IS={self.IS} N={self.N} ISR={self.ISR}\
            NR={self.NR} RS={self.RS} BV={self.BV} IBV={self.IBV} TEMP={self.TEMP}\
            EG={self.EG}"    
        
    @memoized
    def get_i(self, vext, dev):
        if dev.T != self.T:
            self.set_temperature(dev.T)
        if not self.RS:
            i = self._get_i(vext)
            dev.last_vd = vext
        else:
            vd = dev.last_vd if dev.last_vd is not None else 10*self.VT
            vd = newtonRaphson(self._obj_irs, vd, fprime=self._obj_irs_prime,
                        args=(vext, dev), tol=settings.vea, maxiter=500)
            i = self._get_i(vext-vd)
            dev.last_vd = vd
        return i

    def _obj_irs(self, x, vext, dev):
        # obj fn for newton
        return x/self.RS-self._get_i(vext-x)

    def _obj_irs_prime(self, x, vext, dev):
        # obj fn derivative for newton
        # first term
        ret = 1./self.RS
        # disable RS
        RSSAVE = self.RS
        self.RS = 0
        # second term
        ret += self.get_gm(self, 0, (vext-x,), 0, dev)
        # renable RS
        self.RS = RSSAVE
        return ret

    @memoized
    def _safe_exp(self, x):
        return np.exp(x) if x < 70 else np.exp(70) + 10 * x

    def _get_i(self, v):
        # forward
        i_fwd= self.IS * (self._safe_exp(v/(self.N * self.VT)) - 1)
        # recombination
        i_rec= self.ISR* (self._safe_exp(v/(self.NR * self.VT)) - 1)
        # reverse saturation
        i_rev=-self.IS * (self._safe_exp(-(v+self.BV)/(self.VT)) - 1)
        # injection coefficient
        
        return i_fwd+i_rec+i_rev

    @memoized
    def get_gm(self, op_index, ports_v, port_index, dev):
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
        # alter properties based on T
        T = float(T)
        self.EG = self.material.Eg(T) if self.material!=None else self.EG
        self.IS = self.IS*(T/self.T)**(self.XTI/self.N)*np.exp(-units.e*(self.material.Eg(units.Tref) if self.material!=None else self.EG)/(self.N*units.k*T)*(1 - T/self.T))
        self.BV = self.BV - self.TBV*(T - self.T)
        self.RS = self.RS*(1 + self.TRS*(T - self.T))
        self.T = T



    