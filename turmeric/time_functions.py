#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

import math

from scipy.interpolate import InterpolatedUnivariateSpline

time_fun_specs = {'sin': { #VO VA FREQ TD THETA
    'tokens': ({
               'label': 'vo',
               'pos': 0,
               'type': float,
               'needed': True,
               'dest': 'vo',
               'default': None
               },
               {
               'label': 'va',
               'pos': 1,
               'type': float,
               'needed': True,
               'dest': 'va',
               'default': None
               },
               {
               'label': 'freq',
               'pos': 2,
               'type': float,
               'needed': True,
               'dest': 'freq',
               'default': None
               },
               {
               'label': 'td',
               'pos': 3,
               'type': float,
               'needed': False,
               'dest': 'td',
               'default': 0.
               },
               {
               'label': 'theta',
               'pos': 4,
               'type': float,
               'needed': False,
               'dest': 'theta',
               'default': 0
               }
               )
        },'exp': { #EXP(V1 V2 TD1 TAU1 TD2 TAU2)
    'tokens': ({
               'label': 'v1',
               'pos': 0,
               'type': float,
               'needed': True,
               'dest': 'v1',
               'default': None
               },
               {
               'label': 'v2',
               'pos': 1,
               'type': float,
               'needed': True,
               'dest': 'v2',
               'default': None
               },
               {
               'label': 'td1',
               'pos': 2,
               'type': float,
               'needed': False,
               'dest': 'td1',
               'default': 0.
               },
               {
               'label': 'tau1',
               'pos': 3,
               'type': float,
               'needed': True,
               'dest': 'tau1',
               'default': None
               },
               {
               'label': 'td2',
               'pos': 4,
               'type': float,
               'needed': False,
               'dest': 'td2',
               'default': float('inf')
               },
               {
               'label': 'tau2',
               'pos': 5,
               'type': float,
               'needed': False,
               'dest': 'tau2',
               'default': float('inf')
               }
               )
        },'pulse': { #PULSE(V1 V2 TD TR TF PW PER)
    'tokens': ({
               'label': 'v1',
               'pos': 0,
               'type': float,
               'needed': True,
               'dest': 'v1',
               'default': None
               },
               {
               'label': 'v2',
               'pos': 1,
               'type': float,
               'needed': True,
               'dest': 'v2',
               'default': None
               },
               {
               'label': 'td',
               'pos': 2,
               'type': float,
               'needed': False,
               'dest': 'td',
               'default': 0.
               },
               {
               'label': 'tr',
               'pos': 3,
               'type': float,
               'needed': True,
               'dest': 'tr',
               'default': None
               },
               {
               'label': 'tf',
               'pos': 4,
               'type': float,
               'needed': True,
               'dest': 'tf',
               'default': None
               },
               {
               'label': 'pw',
               'pos': 5,
               'type': float,
               'needed': True,
               'dest': 'pw',
               'default': None
               },
               {
               'label': 'per',
               'pos': 6,
               'type': float,
               'needed': True,
               'dest': 'per',
               'default': None
               })
        }, 'sffm': { ## SFFM(VO VA FC MDI FS TD)
    'tokens': ({
               'label': 'vo',
               'pos': 0,
               'type': float,
               'needed': True,
               'dest': 'vo',
               'default': None
               },
               {
               'label': 'va',
               'pos': 1,
               'type': float,
               'needed': True,
               'dest': 'va',
               'default': None
               },
               {
               'label': 'fc',
               'pos': 2,
               'type': float,
               'needed': False,
               'dest': 'fc',
               'default': None
               },
               {
               'label': 'mdi',
               'pos': 3,
               'type': float,
               'needed': True,
               'dest': 'mdi',
               'default': None
               },
               {
               'label': 'fs',
               'pos': 4,
               'type': float,
               'needed': True,
               'dest': 'fs',
               'default': None
               },
               {
               'label': 'td',
               'pos': 5,
               'type': float,
               'needed': False,
               'dest': 'td',
               'default': 0.
               })
        }, 'am': { #AM(sa oc fm fc [td])
    'tokens': ({
               'label': 'sa',
               'pos': 0,
               'type': float,
               'needed': True,
               'dest': 'sa',
               'default': None
               },
               {
               'label': 'oc',
               'pos': 1,
               'type': float,
               'needed': True,
               'dest': 'oc',
               'default': None
               },
               {
               'label': 'fm',
               'pos': 2,
               'type': float,
               'needed': True,
               'dest': 'fm',
               'default': None
               },
               {
               'label': 'fc',
               'pos': 3,
               'type': float,
               'needed': True,
               'dest': 'fc',
               'default': None
               },
               {
               'label': 'td',
               'pos': 4,
               'type': float,
               'needed': False,
               'dest': 'td',
               'default': None
               })
        }
}

class pulse(object):

    def __init__(self, v1, v2, td, tr, pw, tf, per):
        self.v1 = v1
        self.v2 = v2
        self.td = max(td, 0.0)
        self.per = per
        self.tr = tr
        self.tf = tf
        self.pw = pw
        self._type = "V"

    def __call__(self, time):
        """Evaluate the pulse function at the given time."""
        if time is None:
            time = 0
        time = time - self.per * int(time / self.per)
        if time < self.td:
            return self.v1
        elif time < self.td + self.tr:
            return self.v1 + ((self.v2 - self.v1) / (self.tr)) * (time - self.td)
        elif time < self.td + self.tr + self.pw:
            return self.v2
        elif time < self.td + self.tr + self.pw + self.tf:
            return self.v2 + ((self.v1 - self.v2) / (self.tf)) * (time - (self.td + self.tr + self.pw))
        else:
            return self.v1

    def __str__(self):
        return "type=pulse " + \
            self._type.lower() + "1=" + str(self.v1) + " " + \
            self._type.lower() + "2=" + str(self.v2) + \
            " td=" + str(self.td) + " per=" + str(self.per) + \
            " tr=" + str(self.tr) + " tf=" + str(self.tf) + \
            " pw=" + str(self.pw)


class sin(object):

    def __init__(self, vo, va, freq, td=0., theta=0., phi=0.):
        self.vo = vo
        self.va = va
        self.freq = freq
        self.td = td
        self.theta = theta
        self.phi = phi
        self._type = "V"

    def __call__(self, time):
        """Evaluate the sine function at the given time."""
        if time is None:
            time = 0
        if time < self.td:
            return self.vo + self.va*math.sin(math.pi*self.phi/180.)
        else:
            return self.vo + self.va * math.exp((self.td - time)*self.theta) \
                   * math.sin(2*math.pi*self.freq*(time - self.td) + \
                              math.pi*self.phi/180.)

    def __str__(self):
        return "type=sin " + \
            self._type.lower() + "o=" + str(self.vo) + " " + \
            self._type.lower() + "a=" + str(self.va) + \
            " freq=" + str(self.freq) + " theta=" + str(self.theta) + \
            " td=" + str(self.td)


class exp(object):

    def __init__(self, v1, v2, td1, tau1, td2, tau2):
        self.v1 = v1
        self.v2 = v2
        self.td1 = td1
        self.tau1 = tau1
        self.td2 = td2
        self.tau2 = tau2
        self._type = "V"

    def __call__(self, time):
        """Evaluate the exponential function at the given time."""
        if time is None:
            time = 0
        if time < self.td1:
            return self.v1
        elif time < self.td2:
            return self.v1 + (self.v2 - self.v1) * \
                   (1 - math.exp(-1*(time - self.td1)/self.tau1))
        else:
            return self.v1 + (self.v2 - self.v1) * \
                   (1 - math.exp(-1*(time - self.td1)/self.tau1)) + \
                   (self.v1 - self.v2)*(1 - math.exp(-1*(time - self.td2)/self.tau2))

    def __str__(self):
        return "type=exp " + \
            self._type.lower() + "1=" + str(self.v1) + " " + \
            self._type.lower() + "2=" + str(self.v2) + \
            " td1=" + str(self.td1) + " td2=" + str(self.td2) + \
            " tau1=" + str(self.tau1) + " tau2=" + str(self.tau2)


class sffm(object):

    def __init__(self, vo, va, fc, mdi, fs, td):
        self.vo = vo
        self.va = va
        self.fc = fc
        self.mdi = mdi
        self.fs = fs
        self.td = td
        self._type = "V"

    def __call__(self, time):
        """Evaluate the SFFM function at the given time."""
        if time is None:
            time = 0
        if time <= self.td:
            return self.vo
        else:
            return self.vo + self.va*math.sin(2*math.pi*self.fc*(time - self.td) +
                                              self.mdi*math.sin(2*math.pi*self.fs*
                                                                (time - self.td))
                                              )

    def __str__(self):
        return "type=sffm vo=%g va=%g fc=%g mdi=%g fs=%g td=%g" % \
                (self.vo, self.va, self.fc, self.mdi, self.fs, self.td)

class am(object):

    def __init__(self, sa, fc, fm, oc, td):
        self.sa = sa
        self.fc = fc
        self.fm = fm
        self.oc = oc
        self.td = td
        self._type = "V"

    def __call__(self, time):
        """Evaluate the AM function at the given time."""
        if time is None:
            time = 0
        if time <= self.td:
            return 0.
        else:
            return self.sa*(self.oc + math.sin(2*math.pi*self.fm*
                                               (time - self.td)))* \
                   math.sin(2*math.pi*self.fc*(time - self.td))

    def __str__(self):
        return "type=am sa=%g oc=%g fm=%g fc=%g td=%g" % \
                (self.sa, self.oc, self.fm, self.fc, self.td)

class pwl(object):

    def __init__(self, x, y, repeat=False, repeat_time=0, td=0):
        self.x = x
        self.y = y
        self.repeat = repeat
        self.repeat_time = repeat_time
        if self.repeat_time == max(x):
            self.repeat_time = 0
        self.td = td
        self._type = "V"
        self._f = InterpolatedUnivariateSpline(self.x, self.y, k=1)

    def __call__(self, time):
        """Evaluate the PWL function at the given time."""
        time = self._normalize_time(time)
        return self._f(time)

    def _normalize_time(self, time):
        if time is None:
            time = 0
        if time <= self.td:
            time = 0
        elif time > self.td:
            time = time - self.td
            if self.repeat:
                if time > max(self.x):
                    time = (time - max(self.x)) % \
                           (max(self.x) - self.repeat_time) + \
                           self.repeat_time
                else:
                    pass
        return time

    def __str__(self):
        pwl_str = "type=pwl"
        tv = " "
        for x, y in zip(self.x, self.y):
            tv += "%g %g "
        pwl_str += tv
        if self.td:
            pwl_str += "td=%g " % self.td
        if self.repeat:
            pwl_str = "RPT=%g " % self.repeat_time
        return pwl_str[:-1]

