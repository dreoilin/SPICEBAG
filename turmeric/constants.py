# -*- coding: iso-8859-1 -*-

"""Constants useful for building equations and expressions describing
semiconductor physics
"""

import math

e = 1.60217646e-19
T = 300
Tref = 300
k = 1.3806503e-23


def Vth(T=Tref):
    
    return k * T / e

class Material:
    def __init__(self):
        pass;
    def Eg(self, T=Tref):
        """Energy gap of silicon at temperature ``T``

        **Parameters:**

        T : float, optional
            The temperature at which the thermal voltage is to be evaluated.
            If not specified, it defaults to ``constants.Tref``.

        **Returns:**

        Eg : float
            The energy gap, expressed in electron-volt (eV).
        """

        return (self.Eg_0 - self.alpha * T ** 2 / (self.beta + T))  # eV
    
    def ni(self, T=Tref):
        """Intrinsic semiconductor carrier concentration at temperature ``T``

        **Parameters:**

        T : float, optional
            The temperature at which the thermal voltage is to be evaluated.
            If not specified, it defaults to ``constants.Tref``.

        **Returns:**

        ni : float
            The intrinsic carrier concentration.
        """
        return self.n_i_0 * (T / Tref)**(3/2) * math.exp(self.Eg(Tref) / (2 * Vth(Tref)) - self.Eg(T) / (2 * Vth(T)))

class silicon(Material):
    """Silicon class

    **esi**: permittivity of silicon.

    **eox**: permittivity of silicon dioxide.

    """
    def __init__(self):
        self.esi = 104.5 * 10 ** -12  # F/m
        self.eox = 34.5 * 10 ** -12  # F/m
        self.Eg_0=1.16
        self.alpha=0.000702
        self.beta=1108
        self.n_i_0=1.45 * 10 ** 16

#: Silicon class instantiated.
si = silicon()
