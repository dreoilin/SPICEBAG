from abc import ABC, abstractmethod
import re

class Parseable(ABC):

    @abstractmethod
    def __init__(self):
        pass
    
    @classmethod
    @abstractmethod
    def from_line(cls,line):
        print(f"from_line in {__file__} called")
        cls.name = type(cls).__name__
        if not hasattr(cls, '__re__'):
            cls.__re__ = ''
        cls.__re__ = "^" + cls.__re__ + f"{cls.name}" + '(?: +)'.join([rex(o) for o in cls.net_objs])
        match = re.search(r,line.strip().lower())
        try:
            # FOR THIS TO WORK, EACH PARAMETER IN cls.net_objs MUST EVALUATE TO EXACTLY ONE REGEX GROUP
            cls.tokens = [n(g) for n,g in zip(cls.net_objs,match.groups())]
        except AttributeError as e:
            logging.exception(f"Failed to parse element from line\n\t`{line}'\n\tusing the regex `{r}'")

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
