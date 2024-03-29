from abc import ABC, abstractmethod
from turmeric.components.Parseable import Parseable
from turmeric.components.tokens import NoLabel

class Directive(Parseable,ABC):
    def __init__(self, line):
        self.__re__ = '.'
        l = [NoLabel]
        l.extend(self.net_objs)
        self.net_objs = l
        # TODO do the above with .insert or something
        super().__init__(line)

    @abstractmethod
    def __repr__(self):
        pass
    
