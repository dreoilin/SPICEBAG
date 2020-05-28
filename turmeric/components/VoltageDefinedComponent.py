from .Component import Component
import numpy as np

class VoltageDefinedComponent(Component):
    """
    Baseclass for voltage defined components:
    - V independent volage source
    - E vcvs
    - H ccvs
    - L
    """
    
    def __init__(self, line):
        super().__init__(line)
        self.part_id=str(self.tokens[0])

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time=0):
        """
        PAD MATRICES LIKE THIS
        |     +| |     +| | | | || || |
        |     +| |     +| | | | || || |
        |     +|+|     +|*| |=| || || |
        |     +| |     +| | | | || || |
        |++++++| |++++++| |+| |+||+||+|
        D0      + M0    * x0 = ZDC ZT ZAC

        """
        M0  =np.pad(M0  , [(0,1), (0,1)], mode="constant")
        D0  =np.pad(D0  , [(0,1), (0,1)], mode="constant")
        ZDC0=np.pad(ZDC0, [(0,1), (0,0)], mode="constant")
        ZAC0=np.pad(ZAC0, [(0,1), (0,0)], mode="constant")
        ZT0 =np.pad(ZT0 , [(0,1), (0,0)], mode="constant")
        # KCL
        M0[self.n1, -1] = 1.0
        M0[self.n2, -1] = -1.0
        # KVL
        M0[-1, self.n1] = +1.0
        M0[-1, self.n2] = -1.0
        return (M0, ZDC0, ZAC0, D0, ZT0) 
