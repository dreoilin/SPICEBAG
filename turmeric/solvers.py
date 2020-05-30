#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 12:49:45 2020

@author: cian
"""

import logging
from . import options

class Solver():
    """
    Base class
    """
    
    def __init__(self, name=None, steps=None):
        self.name = name
        self._steps = steps
        self._failed = False
        self._finished = False
    
    def __str__(self):
        pass
    
    @property
    def failed(self):
        return self._failed
    
    def fail(self):
        self._failed = True
    
    @property
    def finished(self):
        return self._finished
    
    def _next_step(self):
        pass
    
    def operate_on_M_and_ZDC(self):
        pass
    
class Standard(Solver):
    def __init__(self, name='standard'):
        self.name = name
        self._finished = False
        self._failed = False
        
    def __str__(self):
        return f"Name: {self.name}"
    
    def operate_on_M_and_ZDC(self, M, ZDC, G):
        self._finished = True
        return (M+G, ZDC)
    
class GminStepper(Solver):
    
    def __init__(self, name='gmin_stepping', start=1, stop=20, step=1):
        self.name = name
        self._start = start
        self._stop = stop
        self._step = step
        self._index = 0
        self._failed = False
        self._finished = False
    
    def _next_step(self):
        s = self._start + self._index * self._step
        self._index += 1
        return s
    
    def operate_on_M_and_ZDC(self, M, ZDC, G):
        s = self._next_step()
        # check to see if we are on the last step
        if s >= self._stop:
            self._finished = True
        # scale matrix by Gmin
        G *= 1.0/options.gmin
        # apply new gmin
        G *= 10 ** -s
        return (M + G, ZDC)
        
class SourceStepper(Solver):
    def __init__(self, name ='source_stepping', start=3, stop=0.2, step=0.2):
        self.name = name
        self._start = start
        self._stop = stop
        self._step = step
        self._index = 0
        self._failed = False
        self._finished = False
    
    def _next_step(self):
        s = self._start - self._index * self._step
        self._index += 1
        return s
        
    def operate_on_M_and_ZDC(self, M, ZDC, G):
        s = self._next_step()
        if s <= self._stop:
            self._finished = True
        
        ZDC *= 10 ** -s
        return (M + G, ZDC)
    
def setup_solvers(Gmin=False):
    
    solvers = []
    if options.use_standard_solve_method:
        standard = Standard()
        solvers.append(standard)
    if options.use_gmin_stepping and Gmin:
        gmin_stepping = GminStepper()
        solvers.append(gmin_stepping)
    if options.use_source_stepping and Gmin:
        source_stepping = SourceStepper()
        solvers.append(source_stepping)
    
    return solvers
