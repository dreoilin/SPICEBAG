from abc import ABC, abstractmethod
import logging
import re
from .tokens import rex

class Parseable(ABC):

    def __init__(self,line):
        self.name = type(self).__name__.lower()
        if not hasattr(self, '__re__'):
            self.__re__ = ''
        self.__re__ = "^" + f"{self.name}" + '(?: +)'.join([rex(o) for o in self.net_objs])
        match = re.search(self.__re__,line.strip().lower())
        try:
            # FOR THIS TO WORK, EACH PARAMETER IN self.net_objs MUST EVALUATE TO EXACTLY ONE REGEX GROUP
            self.tokens = [n(g) for n,g in zip(self.net_objs,match.groups())]
        except AttributeError as e:
            logging.exception(f"Failed to parse element from line\n\t`{line}'\n\tusing the regex `{self.__re__}'")

    @property
    def __re__(self):
        return self.__re
    @__re__.setter
    def __re__(self,rex):
        self.__re = rex

    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name
