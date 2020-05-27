"""Constants useful for building equations and expressions describing
semiconductor physics
"""

ZERO_CELSIUS = 273.15
e = 1.60217646e-19
k = 1.3806503e-23

def Kelvin(celsius):
    return celsius+ZERO_CELSIUS

def Vth(T=300):
    return k * T / e

