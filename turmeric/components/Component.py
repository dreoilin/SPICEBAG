import numpy as np
from abc import ABC, abstractmethod
from .Parseable import Parseable

class Component(Parseable):
    """
    Base class for components.
    Defines structure they should follow.
    """

    def __init__(self, line):
        super().__init__(line)

    @abstractmethod
    def __repr__(self):
        pass

    def __str__(self):
        return str(self.value)

    # TODO: what does this do and how is it different from just redefining the functions in a base class?
    #   must be called to define the element!
    def set_char(self, i_function=None, g_function=None):
        if i_function:
            self.i = i_function
        if g_function:
            self.g = g_function

    @abstractmethod
    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        pass

    def g(self, v):
        return 1./self.value

    def i(self, v):
        return 0

