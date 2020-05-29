import logging
import importlib
import numpy as np

from turmeric import results
from turmeric import settings
from turmeric.FORTRAN.DC_SUBRS import gmin_mat
from turmeric.ODEsolvers import BE, odesolvers
from turmeric.analyses.OP import dc_solve
from turmeric.analyses.Analysis import Analysis
from turmeric.components.tokens import ParamDict, Value

class TRAN(Analysis):
    def __init__(self, line):
        self.net_objs = [ParamDict.allowed_params(self, {
            'tstep'  : { 'type' : lambda v: float(Value(v)), 'default' : None },
            'tstop'  : { 'type' : lambda v: float(Value(v)), 'default' : None },
            'tstart' : { 'type' : lambda v: float(Value(v)), 'default' : '0' },
            'method' : { 'type' : lambda v: str(v) if str(v) in odesolvers else settings.default_integration_scheme, 'default' : settings.default_integration_scheme },
            'x0'    : { 'type' : lambda v: [float(val) for val in list(v)], 'default' : [] }
            })]
        super().__init__(line)
        if not len(self.x0) > 0:
            self.x0 = None

    def __repr__(self):
        """
        .TRAN tstep=<Value> tstop=<Value> tstart=<Value> method=<Value> [x0=\[<Value>...\]]
        """
        r = f'.TRAN tstep={self.tstep} tstop={self.tstop} tstart={self.tstart} method={self.method}'
        r += ' x0=['+''.join(str(v) for v in self.x0) + ']' if self.x0 is not None else ''
        return r
    
    def run(self, circ):   
        # setup integration method
        diff_slv = importlib.import_module(f'turmeric.ODEsolvers.{self.method}') if self.method in odesolvers else importlib.import_module(f'turmeric.ODEsolvers.TRAP')
        
        # check params    
        if self.tstart > self.tstop:
            logging.critical(f"tstart ({self.tstart}) > tstop ({self.tstop})")
            raise ValueError("Start value is greater than stop value - can't time travel")
        
        if self.tstep < 0 or self.tstart < 0 or self.tstop < 0:
            logging.critical("t-values are less than 0")
            raise ValueError("Bad t-value. Must be positive")

        locked_nodes = circ.get_locked_nodes()
        
        M, ZDC, D = self.get_reduced_system(circ)
        M_size = M.shape[0]
        NNODES = circ.get_nodes_number()
        self.x0 = self.format_estimate(self.x0, M_size)
        
        logging.info("Building Gmin matrix")

        Gmin_matrix = gmin_mat(settings.gmin, M.shape[0], NNODES-1)
        sol = results.Solution(circ, None, sol_type='TRAN', extra_header='t')
        
        #       tpoint  x    dx
        buf = [(self.tstart, self.x0, None)]
        
        logging.info("Beginning transient")
        
        i = 0
        t = self.tstart
        
        while t < self.tstop:
            if i < diff_slv.rsteps:
                C1, C0 = BE.get_coefs((buf[i][1]), self.tstep)
            else:
                C1, C0 = diff_slv.get_coefs(buf, self.tstep)

            circ.gen_matrices(t)
            ZT = circ.ZT0[1:]
            

            x, error, solved, n_iter = dc_solve(M=(M + C1 * D),
                                                   ZDC=(ZDC + np.dot(D, C0) +ZT), circ=circ,
                                                   Gmin=Gmin_matrix, x0=self.x0,
                                                   time=(t + self.tstep),
                                                   locked_nodes=locked_nodes,
                                                   MAXIT=settings.transient_max_iterations)


            if solved:
                t += self.tstep          # update time step
                self.x0 = x              # update initial estimate
                i += 1              # increment
                row = [t]
                # now append computations
                row.extend(x.transpose().tolist()[0])
                # write to file
                sol.write_data(row)
                dxdt = np.multiply(C1, x) + C0
                buf.append((t, x, dxdt))
                print(f"{t/self.tstop*100} %", flush=True)
                if len(buf) > diff_slv.rsteps:
                    buf.pop(0)
                
            else:
                logging.error("Can't converge with step "+str(self.tstep)+".")
                logging.info("Reduce step or increase max iterations")
                solved = False
                break

        if solved:
            # return the solution object
            logging.info("Transient complete")
            return sol.as_dict(float)
        
        logging.info("Failed to solve")
        return None

    def get_reduced_system(self, circ):
        """
        Auxiliary function to set up the MNA equations for the transient simulation
        
        Parameters
        ----------
        circ : circuit object

        Returns
        -------
        M : reduced M0 matrix
        ZDC : reduced ZDC0 matrix
        D : reduced dynamic matrix

        """
        logging.debug("Getting and reducing MNA equations from circuit")
         
        M = circ.M0[1:, 1:]
        ZDC = circ.ZDC0[1:]
        
        logging.debug("Getting and reducing dynamic matrix D0 from circuit")
        # Once again, if Dynamic matrix has been generated for previous transient, we reuse
        D = circ.D0[1:, 1:]
        
        return (M, ZDC, D)

    def format_estimate(self, x0, dim):
        
        """
        Auxiliary function to format the estimate provided by the DC operating point
        simulation

        Parameters
        ----------
        x0 : initial estimate
        dim : system dimensions

        Returns
        -------
        x0 : numpy array of the initial estimate

        """
        
        if x0 is None:
            logging.info("No initial solution provided... Not ideal")
            x0 = np.zeros((dim, 1))
        else:
            logging.info("Using provided x0")
            if isinstance(x0, dict):
                logging.info("Operating point solution provided as simulation result")
                x0 = [value for value in x0.values()]
                x0 = np.array(x0)
        
        logging.debug("Initial estimate is...")
        logging.debug(x0)
        
        return x0
