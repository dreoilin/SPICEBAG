from abc import ABC, abstractmethod
from turmeric.Directive import Directive

class Analysis(Directive, ABC):
    def __init__(self, line):
        super().__init__(line)

    @abstractmethod
    def __repr__(self):
        pass
    
    @abstractmethod
    def run(self, circ):
        pass
