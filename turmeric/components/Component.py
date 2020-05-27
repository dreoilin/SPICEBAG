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

    @abstractmethod
    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        pass
