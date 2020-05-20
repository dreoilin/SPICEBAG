#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 12:49:45 2020

@author: cian
"""

import logging

class Solver():
    """
    Base class
    """
    
    def __init__(self, name=None, steps=None):
        self.name = name
        self._steps = steps
        self._enabled = False
        self._failed = False
        self._finished = False
    
    def __str__(self):
        pass
    
    @property
    def enabled(self):
        return self._enabled
    
    def enable(self):
        if self._failed:
            logging.error("Cannot re-enable a solver")
            raise RuntimeError
        self._enabled = True
    
    @property
    def failed(self):
        return self._failed
    
    def fail(self):
        if self._enabled:
            self._enabled = False
        self._failed = True
    
    @property
    def finished(self):
        return self._finished
    
    def _next_step(self):
        pass
    
    def augment_M_and_ZDC(self):
        pass
    
class Standard(Solver):
    def __init__(self, name='standard'):
        self.name = name
        self._steps = None
        self._enabled = False
        self._failed = False
        
    def __str__(self):
        return f"Name: {self.name}"
    
    def augment_M_and_ZDC(self, M, ZDC, G):
        self._finished = True
        return (M+G, ZDC)
    
class GminStepper(Solver):
    
    def __init__(self, name='gmin_stepping', steps=None):
        self.name = name
        self._steps = steps
        self._enabled = False
        self._failed = False
        self._finished = False
    
    def print_steps(self):
        print(self._steps)
    
    def more_steps(self):
        return len(self._steps)
    
    def _next_step(self):
        if self.more_steps():
            return self._steps.pop(0)
        else:
            logging.debug("No more steps available")
            return None
    
    def augment_M_and_ZDC(self, M, ZDC, G):
        # check to see if we are on the last step
        # mark as finished
        if self.more_steps == 1:
            self._finished = True
        # get the step
        step = self._next_step()
        # None error is bad usage
        if step is not None:
            G *= 10 ** step
            return (M + G, ZDC)
        else:
            raise AttributeError
        
class SourceStepper(Solver):
    def __init__(self, name ='source_stepping', steps = None):
        self.name = name
        self._steps = None
        self._enabled = False
        self._failed = False
        self._finished = False
    
    def _next_step(self):
        if self.more_steps():
            return self._steps.pop(0)
        else:
            logging.debug("No more steps available")
            return None
        
    def augment_M_and_ZDC(self, M, ZDC, G):
        step = self._next_step()
        
        if not self.more_steps():
            self.finished = True
        
        if step is not None:
            ZDC *= step
            return (M + G, ZDC)
        else:
            raise AttributeError