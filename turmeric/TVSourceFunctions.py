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

class AM(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'fc'   : { 'type': float, 'default': None },
                'fm'   : { 'type': float, 'default': None },
                'oc'   : { 'type': float, 'default': None },
                'sa'   : { 'type': float, 'default': None },
                'td'   : { 'type': float, 'default': None }
                }
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
        if time <= self.td:
            return 0.
        else:
            return self.sa*(self.oc + math.sin(2*math.pi*self.fm*(time - self.td)))*math.sin(2*math.pi*self.fc*(time - self.td))

class EXP(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'tau1' : { 'type': float, 'default': None        },
                'tau2' : { 'type': float, 'default': float('inf')},
                'td1'  : { 'type': float, 'default': 0           },
                'td2'  : { 'type': float, 'default': float('inf')},
                'v1'   : { 'type': float, 'default': None        },
                'v2'   : { 'type': float, 'default': None        }
                }
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
        if time < self.td1:
            return self.v1
        elif time < self.td2:
            return self.v1 + (self.v2 - self.v1) * (1 - math.exp(-1*(time - self.td1)/self.tau1))
        else:
            return (self.v1 + (self.v2 - self.v1) * (1 - math.exp(-1*(time - self.td1)/self.tau1)) 
                    + (self.v1 - self.v2)*(1 - math.exp(-1*(time - self.td2)/self.tau2)))


class PULSE(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'per' : { 'type': float, 'default': None },
                'pw'  : { 'type': float, 'default': None },
                'td'  : { 'type': float, 'default': 0    },
                'tf'  : { 'type': float, 'default': None },
                'tr'  : { 'type': float, 'default': None },
                'v1'  : { 'type': float, 'default': None },
                'v2'  : { 'type': float, 'default': None }
                }
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
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

class SFFM(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'fc'  : { 'type': float, 'default': None },
                'fs'  : { 'type': float, 'default': None },
                'mdi' : { 'type': float, 'default': None },
                'td'  : { 'type': float, 'default': 0    },
                'va'  : { 'type': float, 'default': None },
                'vo'  : { 'type': float, 'default': None }
                }
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
        if time <= self.td:
            return self.vo
        else:
            return self.vo + self.va*math.sin(2*math.pi*self.fc*(time - self.td) + self.mdi*math.sin(2*math.pi*self.fs*(time - self.td)))

class SIN(TVSourceFunction):
    def __init__(self, paramdict):
        self.params = {
                'freq' : { 'type': float, 'default': None },
                'phi'  : { 'type': float, 'default': 0    },
                'td'   : { 'type': float, 'default': 0    },
                'theta': { 'type': float, 'default': 0    },
                'va'   : { 'type': float, 'default': None },
                'vo'   : { 'type': float, 'default': None }
                }
        super().__init__(paramdict)

    def __call__(self, time):
        time = 0 if time is None else time
        if time < self.td:
            return self.vo + self.va*math.sin(math.pi*self.phi/180.)
        else:
            return self.vo + self.va * math.exp((self.td - time)*self.theta) * math.sin(2*math.pi*self.freq*(time - self.td) + math.pi*self.phi/180.)

tvsourcefunctions = {
        'am' : AM,
        'exp' : EXP,
        'pulse' : PULSE
        'sffm' : SFFM,
        'sin' : SIN,
        }

