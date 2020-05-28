import numpy as np
import logging

from turmeric import results
from turmeric import complex_solve
from turmeric.analyses.Analysis import Analysis
from turmeric.components.tokens import ParamDict, Value

SWEEP_LOG = "LOG"
SWEEP_LIN = "LIN"

j = np.complex('j')

class AC(Analysis):
    
    """
    ~~~~~~~~~~~~~~~~~~
    AC Analysis Class:
    ~~~~~~~~~~~~~~~~~~

    Provides a method for an AC analysis of a netlist for a 
    specified range of frequencies.
    
    Currently, only linear circuits are supported
    
    """
    
    def __init__(self, line):
        self.net_objs = [ParamDict.allowed_params(self,{
            'type'   : { 'type' : str   , 'default' : SWEEP_LOG }, # Should really be an enumeration of values, but grand for now
            'nsteps' : { 'type' : int   , 'default' : None      },
            'start'  : { 'type' : lambda v: float(Value(v)) , 'default' : None      },
            'stop'   : { 'type' : lambda v: float(Value(v)) , 'default' : None      }
            })]
        super().__init__(line)

    def __repr__(self):
        """
        .ac [type=LOG/LIN] nsteps=steps start=start stop=stop
        """
        return f".AC {f'type={self.type} ' if hasattr(self,'type') else ''}nsteps={self.nsteps} start={self.start} stop={self.stop}"

    def run(self, circ, sweep_type=None):
        
        """
        ~~~~~~~~~~~~~~~~~~
        AC Analysis Method:
        ~~~~~~~~~~~~~~~~~~
        
        Mathematically, the problem definition is:
                
                D x j2piw + M = ZAC, where
                
                D : reduced dynamic matrix
                w : variable frequency of the harmonic source
                M : reduced conductance matrix
                ZAC : source contribution
                
        The method solves this system of equations for a varying frequency.
        
        The linear system of complex valued components is passed to a mapping
        module which reduces the n complex equations to 2n real valued linear
        equations, and returns the n variable complex solution.
        
        RETURNS:
            
            sol : solution object as a dictionary to the main method
        
        """
        
        # check step/start/stop parameters
        if self.start == 0:
            raise ValueError("ac_analysis(): AC analysis has start frequency = 0")
        if self.start > self.stop:
            raise ValueError("ac_analysis(): AC analysis has start > stop")
        if self.nsteps < 2 and not self.start == self.stop:
            raise ValueError("ac_analysis(): AC analysis has number of points < 2 & start != stop")
        
        if self.type.upper() == SWEEP_LOG or self.type is None:
            fs = np.logspace(int(self.start), np.log(int(self.stop)), num=int(self.nsteps), endpoint=True)
        elif self.type.upper() == SWEEP_LOG:
            fs = np.linspace(int(self.start), int(self.stop), num=int(self.nsteps), endpoint=True)
        else:
            raise ValueError(f"ac_analysis(): unknown sweep type {self.type}")

        logging.info(f"Starting AC analysis")
        logging.info(f"Start Freq. : {self.start} Hz\tStop Freq. : {self.stop} Hz\n \
                     Using {self.nsteps} points on a {self.type.lower()} axis")    
        
        # get and reduce MNA equations
        M = circ.M0[1:, 1:]
        ZAC = circ.ZAC0[1:]
        D = circ.D0[1:, 1:]
        # nonlinear cicuits currently not implemented
        if circ.is_nonlinear():
            raise ValueError

        # set up the solution object
        sol = results.Solution(circ, sol_type='AC', extra_header='f')
        
        # solve for all specified frequencies
        for f in fs:
            IMP = f * np.pi * 2 * j * D
            x = complex_solve.solver((M + IMP), -ZAC)
            data = [f]
            data.extend(x.transpose().tolist()[0])
            sol.write_data(data)
       
        sol.close()
        
        return sol.as_dict(v_type=complex)
