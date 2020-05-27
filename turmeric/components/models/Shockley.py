from ... import units
from ... import utilities
from math import isinf, sqrt
import numpy as np
from scipy.optimize import newton

DEFAULT_AF   = 1. 
DEFAULT_AREA = 1.0
DEFAULT_BV   = float('inf') 
DEFAULT_CJ0  = 0.0 
DEFAULT_CP   = .0 
DEFAULT_EG   = 1.11
DEFAULT_FC   = .5 
DEFAULT_FFE  = 1. 
DEFAULT_IBV  = 1e-3 
DEFAULT_IKF  = float('inf') 
DEFAULT_IS   = 1e-14  
DEFAULT_ISR  = 0.0  
DEFAULT_KF   = .0 
DEFAULT_M    = .5 
DEFAULT_N    = 1.0 
DEFAULT_NBV  = 1.0 
DEFAULT_NR   = 2.0 
DEFAULT_RS   = 0.0  
DEFAULT_TBV  = 0.0
DEFAULT_TEMP = 26.85
DEFAULT_T    = units.Kelvin(celsius=DEFAULT_TEMP)
DEFAULT_TM1  = 0.0
DEFAULT_TM2  = 0.0
DEFAULT_TRS  = 0.0
DEFAULT_TT   = .0 
DEFAULT_TTT1 = 0.0
DEFAULT_TTT2 = 0.0
DEFAULT_VJ   = .7 
DEFAULT_XTI  = 3.0


class Material:
    def __init__(self):
        pass;
    def Eg(self, T=DEFAULT_T):
        return (self.Eg_0 - self.alpha * T ** 2 / (self.beta + T))  # eV
    
    def ni(self, T=DEFAULT_T):
        return self.n_i_0 * (T / Tref)**(3/2) * math.exp(self.Eg(Tref) / (2 * Vth(Tref)) - self.Eg(T) / (2 * Vth(T)))

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
    def __init__(self, name, IS=None, N=None, NBV=None, ISR=None, NR=None, RS=None,
                 CJ0=None, M=None, VJ=None, FC=None, CP=None, TT=None,
                 BV=None, IBV=None, IKF=None, KF=None, AF=None, FFE=None, TEMP=None,
                 XTI=None, EG=None, TBV=None, TRS=None, TTT1=None, TTT2=None,
                 TM1=None, TM2=None, material=si):
        self.name = name
        self.IS   = float(IS) if IS is not None else DEFAULT_IS
        self.N    = float(N) if N is not None else DEFAULT_N
        self.NBV  = float(NBV) if NBV is not None else DEFAULT_NBV
        self.ISR  = float(ISR) if ISR is not None else DEFAULT_ISR
        self.NR   = float(NR) if NR is not None else DEFAULT_NR
        self.RS   = float(RS) if RS is not None else DEFAULT_RS
        self.CJ0  = float(CJ0) if CJ0 is not None else DEFAULT_CJ0
        self.M    = float(M) if M is not None else DEFAULT_M
        self.VJ   = float(VJ) if VJ is not None else DEFAULT_VJ
        self.FC   = float(FC) if FC is not None else DEFAULT_FC
        self.CP   = float(CP) if CP is not None else DEFAULT_CP
        self.TT   = float(TT) if TT is not None else DEFAULT_TT
        self.BV   = float(BV) if BV is not None else DEFAULT_BV
        self.IBV  = float(IBV) if IBV is not None else DEFAULT_IBV
        self.IKF  = float(IKF) if IKF is not None else DEFAULT_IKF
        self.KF   = float(KF) if KF is not None else DEFAULT_KF
        self.AF   = float(AF) if AF is not None else DEFAULT_AF
        self.FFE  = float(FFE) if FFE is not None else DEFAULT_FFE
        self.TEMP = float(TEMP) + ZERO_CELSIUS if TEMP is not None else DEFAULT_TEMP
        self.XTI  = float(XTI) if XTI is not None else DEFAULT_XTI
        self.EG   = float(EG) if EG is not None else DEFAULT_EG
        self.TBV  = float(TBV) if TBV is not None else DEFAULT_TBV
        self.TRS  = float(TRS) if TRS is not None else DEFAULT_TRS
        self.TTT1 = float(TTT1) if TTT1 is not None else DEFAULT_TTT1
        self.TTT2 = float(TTT2) if TTT2 is not None else DEFAULT_TTT2
        self.TM1  = float(TM1) if TM1 is not None else DEFAULT_TM1
        self.TM2  = float(TM2) if TM2 is not None else DEFAULT_TM2
        self.T    = DEFAULT_T
        self.last_vd = None
        self.VT   = units.k * self.T / units.e
        self.material=material

    def print_model(self):
        print(str(self))

    @utilities.memoize
    def get_i(self, vext, dev):
        if dev.T != self.T:
            self.set_temperature(dev.T)
        if not self.RS:
            i = self._get_i(vext) * dev.AREA
            dev.last_vd = vext
        else:
            vd = dev.last_vd if dev.last_vd is not None else 10*self.VT
            vd = newton(self._obj_irs, vd, fprime=self._obj_irs_prime,
                        args=(vext, dev), tol=options.vea, maxiter=500)
            i = self._get_i(vext-vd)
            dev.last_vd = vd
        return i

    def _obj_irs(self, x, vext, dev):
        # obj fn for newton
        return x/self.RS-self._get_i(vext-x)*dev.AREA

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

    def _safe_exp(self, x):
        return np.exp(x) if x < 70 else np.exp(70) + 10 * x

    def _get_i(self, v):
        i_fwd= self.IS * (self._safe_exp(v/(self.N * self.VT)) - 1)
        i_rec= self.ISR* (self._safe_exp(v/(self.NR * self.VT)) - 1)
        i_rev=-self.IS * (self._safe_exp(-(v+self.BV)/(self.NBV *self.VT)) - 1)
        k_inj = 1
        if (not isinf(self.IKF)) and (self.IKF>0) and (i_fwd>0):
            k_inj = sqrt(self.IKF/(self.IKF+i_fwd))
        
        return k_inj*i_fwd+i_rec+i_rev

    @utilities.memoize
    def get_gm(self, op_index, ports_v, port_index, dev):
        if dev.T != self.T:
            self.set_temperature(dev.T)
        v=ports_v[0]
        gm = self.IS / (self.N * self.VT) *\
            self._safe_exp(v / (self.N * self.VT)) +\
            -self.IS/self.VT * (self._safe_exp(-(v+self.BV)/self.VT)) +\
            self.ISR / (self.NR * self.VT) *\
            self._safe_exp(v / (self.NR * self.VT))
        
        if self.RS != 0.0:
            gm = 1. / (self.RS + 1. / (gm + 1e-3*options.gmin))
        return dev.AREA * gm

    def __str__(self):
        strm = ".model D %s IS=%g N=%g ISR=%g NR=%g RS=%g CJ0=%g M=%g " + \
               "VJ=%g FC=%g CP=%g TT=%g BV=%g IBV=%g KF=%g AF=%g FFE=%g " + \
               "TEMP=%g XTI=%g EG=%g TBV=%g TRS=%g TTT1=%g TTT2=%g TM1=%g " + \
               "TM2=%g"
        return strm % (self.name, self.IS, self.N, self.ISR, self.NR, self.RS,
                      self.CJ0, self.M, self.VJ, self.FC, self.CP, self.TT,
                      self.BV, self.IBV, self.KF, self.AF, self.FFE, self.TEMP,
                      self.XTI, self.EG, self.TBV, self.TRS, self.TTT1,
                      self.TTT2, self. TM1, self. TM2)

    def set_temperature(self, T):
        T = float(T)
        self.EG = self.material.Eg(T) if self.material!=None else self.EG
        self.IS = self.IS*(T/self.T)**(self.XTI/self.N)* \
                  np.exp(-units.e*(self.material.Eg(units.Tref) if self.material!=None else self.EG)/\
                         (self.N*units.k*T)*
                         (1 - T/self.T))
        self.BV = self.BV - self.TBV*(T - self.T)
        self.RS = self.RS*(1 + self.TRS*(T - self.T))
        self.T = T
