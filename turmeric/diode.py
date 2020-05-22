#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from math import isinf, sqrt
import numpy as np

from scipy.optimize import newton

from . import constants
from . import utilities
from . import options

damping_factor = 4.

class diode(object):
    """A diode element.

    **Parameters:**

    n1, n2 : string
        The diode anode and cathode.
    model : model instance
        The diode model providing the mathemathical modeling.
    ic : float
        The diode initial voltage condition for transient analysis
        (ie :math:`V_D = V(n_1) - V(n_2)` at :math:`t = 0`).
    off : bool
         Whether the diode should be initially assumed to be off when
         computing an OP.

    The other are the physical parameters reported in the following table:

    +---------------+-------------------+-----------------------------------+
    | *Parameter*   | *Default value*   | *Description*                     |
    +===============+===================+===================================+
    | AREA          | 1.0               | Area multiplier                   |
    +---------------+-------------------+-----------------------------------+
    | T             | circuit temp      | Operating temperature             |
    +---------------+-------------------+-----------------------------------+

    """

    def __init__(self, part_id, n1, n2, model, AREA=None, T=None, ic=None, off=False):
        self.part_id = part_id
        self.is_nonlinear = True
        self.is_symbolic = True
        self.dc_guess = [0.425]
        class _dev_class(object):
            pass
        self.device = _dev_class()
        self.device.AREA = AREA if AREA is not None else 1.0
        self.device.T = T
        self.device.last_vd = .425
        self.n1 = n1
        self.n2 = n2
        self.ports = ((self.n1, self.n2),)
        self.model = model
        if self.device.T is None:
            self.device.T = constants.T

        if ic is not None:  # fixme
            print("(W): ic support in diodes is very experimental.")
            self.dc_guess = ic
        self.ic = ic
        self.off = off
        if self.off:
            if self.ic is None:
                self.ic = 0
            else:
                print("(W): IC statement in diodes takes precedence over OFF.")
                print("(W): If you are performing a transient simulation with uic=2,")
                print("(W): you may want to check the initial value.")

    def _get_T(self):
        return self.device.T

    def set_temperature(self, T):
        """Set the operating temperature IN KELVIN degrees
        """
        # this automatically makes the memoization cache obsolete. self.device
        # is in fact passed as one of the arguments, hashed and stored:
        # if it changes, the old cache will return misses.
        self.device.T = T

    def __str__(self):
        rep = "%s area=%g T=%g" % (
            self.model.name, self.device.AREA, self._get_T())
        if self.ic is not None:
            rep = rep + " ic=" + str(self.ic)
        elif self.off:
            rep += " off"
        return rep

    def get_output_ports(self):
        return self.ports

    def get_drive_ports(self, op):
        if not op == 0:
            raise ValueError('Diode %s has no output port %d' %
                             (self.part_id, op))
        return self.ports

    def istamp(self, ports_v, time=0, reduced=True):
        """Get the current matrix

        A matrix corresponding to the current flowing in the element
        with the voltages applied as specified in the ``ports_v`` vector.

        **Parameters:**

        ports_v : list
            A list in the form: [voltage_across_port0, voltage_across_port1, ...]
        time: float
            the simulation time at which the evaluation is performed.
            It has no effect here. Set it to None during DC analysis.

        """
        v = ports_v[0]
        i = self.model.get_i(self.model, v, self.device)
        istamp = np.array((i, -i), dtype=np.float64)
        indices = ((self.n1 - 1*reduced, self.n2 - 1*reduced), (0, 0))
        if reduced:
            delete_i = [pos for pos, ix in enumerate(indices[0]) if ix == -1]
            istamp = np.delete(istamp, delete_i, axis=0)
            indices = tuple(zip(*[(ix, j) for ix, j in zip(*indices) if ix != -1]))
        return indices, istamp

    def i(self, op_index, ports_v, time=0):  # with gmin added
        v = ports_v[0]
        i = self.model.get_i(self.model, v, self.device)
        return i

    def gstamp(self, ports_v, time=0, reduced=True):
        """Returns the differential (trans)conductance wrt the port specified by port_index
        when the element has the voltages specified in ports_v across its ports,
        at (simulation) time.

        ports_v: a list in the form: [voltage_across_port0, voltage_across_port1, ...]
        port_index: an integer, 0 <= port_index < len(self.get_ports())
        time: the simulation time at which the evaluation is performed. Set it to
        None during DC analysis.
        """
        indices = ([self.n1 - 1]*2 + [self.n2 - 1]*2,
                   [self.n1 - 1, self.n2 - 1]*2)
        gm = self.model.get_gm(self.model, 0, utilities.tuplinator(ports_v), 0, self.device)
        if gm == 0:
            gm = options.gmin*2
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
            raise Exception("Attepted to evaluate a diode's gm on an unknown port.")
        gm = self.model.get_gm(self.model, op_index, utilities.tuplinator(ports_v), port_index, self.device)
        return gm

    def get_op_info(self, ports_v_v):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the diode terminals.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v_v[0][0])
        idiode = self.i(0, (vn1n2,))
        gmdiode = self.g(0, (vn1n2,), 0)
        op_keys = ["Part ID", "V(n1-n2) [V]", "I(n1-n2) [A]", "P [W]",
                "gm [A/V]", u"T [\u00b0K]"]
        op_info = [self.part_id.upper(), vn1n2, idiode, vn1n2*idiode, gmdiode,
                   self._get_T()]
        return op_keys, op_info

    def get_netlist_elem_line(self, nodes_dict):
        ext_n1, ext_n2 = nodes_dict[self.n1], nodes_dict[self.n2]
        ret = "%s %s %s %s" % (self.part_id, ext_n1, ext_n2, self.model.name)
        # append the optional part:
        # [<AREA=float> <T=float> <IC=float> <OFF=boolean>]
        ret += " AREA=%g" % self.device.AREA
        if self.device.T is not None:
            ret += " T=%g" % self.device.T
        if self.ic is not None:
            ret += " IC=%g" % self.ic
        if self.off:
            ret += " OFF=1"
        return ret
        
IS_DEFAULT = 1e-14  # saturation current A
N_DEFAULT = 1.0 # forvard branch ideality factor
NBV_DEFAULT = 1.0 # breakdown ideality factor
ISR_DEFAULT = 0.0  # recombination current parameter A
NR_DEFAULT = 2.0 # emission coefficient for Isr
RS_DEFAULT = 0.0  # series resistance ohm
CJ0_DEFAULT = 0.0 # zero bias junction capacitance
M_DEFAULT = .5 # grading coefficient
VJ_DEFAULT = .7 # junction built-in potential
FC_DEFAULT = .5 # forward bias depletion capacitance coefficient
CP_DEFAULT = .0 # linear capacitance F
TT_DEFAULT = .0 # transit time s
BV_DEFAULT = float('inf') # reverse breakdown voltage
IBV_DEFAULT = 1e-3 # reverse breakdown current IBV=-I(-BV)
IKF_DEFAULT = float('inf') # high-injection knee current A
KF_DEFAULT = .0 # flicker noise coefficient
AF_DEFAULT = 1. # flicker noise exponent
FFE_DEFAULT = 1. # flicker noise frequency exponent
TEMP_DEFAULT = 26.85 # temperature
XTI_DEFAULT = 3.0 # saturation current exponent
EG_DEFAULT = 1.11 # band gap
TBV_DEFAULT = 0.0 # BV linear temperature coefficient 1/◦C
TRS_DEFAULT = 0.0 # RS linear temperature coefficient 1/◦C
TTT1_DEFAULT = 0.0 # TT linear temperature coefficient
TTT2_DEFAULT = 0.0 # TT quadratic temperature coefficient
TM1_DEFAULT = 0.0 # M linear temperature coefficient
TM2_DEFAULT = 0.0 # M quadratic temperature coefficient
T_DEFAULT = utilities.Celsius2Kelvin(26.85)
AREA_DEFAULT = 1.0 # area

class diode_model(object):
    """A diode model implementing the `Shockley diode equation
    <http://en.wikipedia.org/wiki/Shockley_diode_equation#Shockley_diode_equation>`__.

    Currently the capacitance modeling part is missing.

    The principal parameters are:

    +---------------+-------------------+-----------------------------------+
    | *Parameter*   | *Default value*   | *Description*                     |
    +===============+===================+===================================+
    | IS            | 1e-14 A           | Specific current                  |
    +---------------+-------------------+-----------------------------------+
    | N             | 1.0               | Emission coefficient              |
    +---------------+-------------------+-----------------------------------+
    | ISR           | 0.0 A             | Recombination current             |
    +---------------+-------------------+-----------------------------------+
    | NR            | 2.0               | Recombination coefficient         |
    +---------------+-------------------+-----------------------------------+
    | RS            | 0.0 ohm           | Series resistance per unit area   |
    +---------------+-------------------+-----------------------------------+

    please refer to a textbook description of the Shockley diode equation
    or to the source file ``diode.py`` file for the other parameters.

    """
    def __init__(self, name, IS=None, N=None, NBV=None, ISR=None, NR=None, RS=None,
                 CJ0=None, M=None, VJ=None, FC=None, CP=None, TT=None,
                 BV=None, IBV=None, IKF=None, KF=None, AF=None, FFE=None, TEMP=None,
                 XTI=None, EG=None, TBV=None, TRS=None, TTT1=None, TTT2=None,
                 TM1=None, TM2=None, material=constants.si):
        self.name = name
        self.IS = float(IS) if IS is not None else IS_DEFAULT
        self.N = float(N) if N is not None else N_DEFAULT
        self.NBV = float(NBV) if NBV is not None else NBV_DEFAULT
        self.ISR = float(ISR) if ISR is not None else ISR_DEFAULT
        self.NR = float(NR) if NR is not None else NR_DEFAULT
        self.RS = float(RS) if RS is not None else RS_DEFAULT
        self.CJ0 = float(CJ0) if CJ0 is not None else CJ0_DEFAULT
        self.M = float(M) if M is not None else M_DEFAULT
        self.VJ = float(VJ) if VJ is not None else VJ_DEFAULT
        self.FC = float(FC) if FC is not None else FC_DEFAULT
        self.CP = float(CP) if CP is not None else CP_DEFAULT
        self.TT = float(TT) if TT is not None else TT_DEFAULT
        self.BV = float(BV) if BV is not None else BV_DEFAULT
        self.IBV = float(IBV) if IBV is not None else IBV_DEFAULT
        self.IKF = float(IKF) if IKF is not None else IKF_DEFAULT
        self.KF = float(KF) if KF is not None else KF_DEFAULT
        self.AF = float(AF) if AF is not None else AF_DEFAULT
        self.FFE = float(FFE) if FFE is not None else FFE_DEFAULT
        self.TEMP = utilities.Celsius2Kelvin(float(TEMP)) if TEMP is not None else TEMP_DEFAULT
        self.XTI = float(XTI) if XTI is not None else XTI_DEFAULT
        self.EG = float(EG) if EG is not None else EG_DEFAULT
        self.TBV = float(TBV) if TBV is not None else TBV_DEFAULT
        self.TRS = float(TRS) if TRS is not None else TRS_DEFAULT
        self.TTT1 = float(TTT1) if TTT1 is not None else TTT1_DEFAULT
        self.TTT2 = float(TTT2) if TTT2 is not None else TTT2_DEFAULT
        self.TM1 = float(TM1) if TM1 is not None else TM1_DEFAULT
        self.TM2 = float(TM2) if TM2 is not None else TM2_DEFAULT
        self.T = T_DEFAULT
        self.last_vd = None
        self.VT = constants.Vth(self.T)
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
        strm = ".model diode %s IS=%g N=%g ISR=%g NR=%g RS=%g CJ0=%g M=%g " + \
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
                  np.exp(-constants.e*(self.material.Eg(constants.Tref) if self.material!=None else self.EG)/\
                         (self.N*constants.k*T)*
                         (1 - T/self.T))
        self.BV = self.BV - self.TBV*(T - self.T)
        self.RS = self.RS*(1 + self.TRS*(T - self.T))
        self.T = T

