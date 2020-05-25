from .Component import Component
from .. import utilities
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

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0):
        """
        PAD MATRICES LIKE THIS
        |     +| |     +| | | | || || |
        |     +| |     +| | | | || || |
        |     +|+|     +|*| |=| || || |
        |     +| |     +| | | | || || |
        |++++++| |++++++| |+| |+||+||+|
        D0      + M0    * x0 = ZDC ZT ZAC

        """
        #print("SUPERVD")
        M0  =np.pad(M0  , [(0,1), (0,1)], mode="constant")
        D0  =np.pad(D0  , [(0,1), (0,1)], mode="constant")
        ZDC0=np.pad(ZDC0, [(0,1), (0,0)], mode="constant")
        ZAC0=np.pad(ZAC0, [(0,1), (0,0)], mode="constant")
        ZT0 =np.pad(ZT0 , [(0,1), (0,0)], mode="constant")
        #M0   = utilities.expand_matrix(M0, add_a_row=True, add_a_col=True)
        #D0   = utilities.expand_matrix(M0, add_a_row=True, add_a_col=True)
        #ZDC0 = utilities.expand_matrix(ZDC0, add_a_row=True, add_a_col=False)
        #ZAC0 = utilities.expand_matrix(ZAC0, add_a_row=True, add_a_col=False)
        ## TODO: optimise for ZT0 as produced a lot
        #ZT0  = utilities.expand_matrix(ZT0, add_a_row=True, add_a_col=False)
        #print(f"VD M0 PRE-KIRCHOFF: {M0}")
        # KCL
        M0[self.n1, -1] = 1.0
        M0[self.n2, -1] = -1.0
        # KVL
        M0[-1, self.n1] = +1.0
        M0[-1, self.n2] = -1.0
        #print(f"VD M0 POST-KIRCHOFF: {M0}")
        return (M0, ZDC0, ZAC0, D0, ZT0) 
