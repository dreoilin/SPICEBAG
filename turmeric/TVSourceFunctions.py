from abc import ABC, abstractmethod
import math

class TVSourceFunction(ABC):
    """
    Base class for all time-varying source functions.

    paramdict - parsed dictionary whose entries are the name and value of the arguments to the time function
    """
    def __init__(self, paramdict):
        self.name = type(self).__name__.lower()

        for name, rpdesc in self.params.items():
            if name in paramdict:
                # This will overwrite any previous value for rpk
                setattr(self,name,rpdesc['type'](paramdict[name]))
            elif rpdesc['default'] is not None:
                setattr(self,name,rpdesc['type'](rpdesc['default']))
            else:
                raise ValueError(f'Missing non-default parameter {name} for {self.name} source')

    @abstractmethod
    def __call__(self, time):
        pass

    def __repr__(self):
        return f'{self.name} ' + ' '.join([f'{k}={getattr(self,k)}' for k in self.params])

class SIN(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'vo'   : { 'type': float, 'default': None },
                'va'   : { 'type': float, 'default': None },
                'freq' : { 'type': float, 'default': None },
                'td'   : { 'type': float, 'default': 0    },
                'theta': { 'type': float, 'default': 0    },
                'phi'  : { 'type': float, 'default': 0    }}
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
        if time < self.td:
            return self.vo + self.va*math.sin(math.pi*self.phi/180.)
        else:
            return self.vo + self.va * math.exp((self.td - time)*self.theta) * math.sin(2*math.pi*self.freq*(time - self.td) + math.pi*self.phi/180.)


tvsourcefunctions = {
        'sin' : SIN
        }

