import numpy as np
import logging

from turmeric import results
from turmeric import complex_solve
from turmeric.analyses.Analysis import Analysis
from turmeric.components.tokens import ParamDict, Value

SWEEP_LOG = "LOG"
SWEEP_LIN = "LIN"

class AC(Analysis):
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
        .AC [type=LOG/LIN] nsteps=steps start=start stop=stop
        """
        return f".AC {f'type={self.type} ' if hasattr(self,'type') else ''}nsteps={self.nsteps} start={self.start} stop={self.stop}"

    def run(self, circ, sweep_type=None):
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
        
        # get the MNA matrices from the circuit object
        M0 = circ.M0
        ZAC0 = circ.ZAC0
        D0 = circ.D0
            
        # reduce the matrices
        M = M0[1:, 1:]
        ZAC = ZAC0[1:]
        D = D0[1:, 1:]
        
        if circ.is_nonlinear():
            logging.error("AC analysis does not currently support analysis of \
                          non-linear circuits")
            raise ValueError

        sol = results.Solution(circ, sol_type='AC', extra_header='f')
        

        j = np.complex('j')
        
        for f in fs:
            # evaluate the impedance at
            # the current frequency
            IMP = f * np.pi * 2 * j * D
            # solve using the complex solver
            x = complex_solve.solver((M + IMP), -ZAC)
            # start row with frequency
            row = [f]
            # now append computations
            row.extend(x.transpose().tolist()[0])
            # write to file
            sol.write_data(row)
       
        sol.close()
        
        return sol.as_dict(v_type=complex)
