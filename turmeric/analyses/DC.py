import logging
import numpy as np

# linear components
from turmeric import components
from turmeric import settings
from turmeric import results
from turmeric.analyses.OP import op_analysis
from turmeric.analyses.Analysis import Analysis
from turmeric.components.tokens import ParamDict, Value

class DC(Analysis):
    def __init__(self, line):
        self.net_objs = [ParamDict.allowed_params(self, {
            'src'   : { 'type' : str                       , 'default': None },
            'start' : { 'type' : lambda v: float(Value(v)) , 'default': None },
            'stop'  : { 'type' : lambda v: float(Value(v)) , 'default': None },
            'step'  : { 'type' : lambda v: float(Value(v)) , 'default': None },
            'x0'    : { 'type' : lambda v: [float(val) for val in list(v)], 'default' : [] }
            })]
        super().__init__(line)
        if not len(self.x0) > 0:
            self.x0 = None

    def __repr__(self):
        """
        .DC src=<src_part_id> start=<Value> stop=<Value> step=<Value> [x0=\[<Value>...\]]
        """
        r = f".DC src={self.src} start={self.start} stop={self.stop} step={self.step}"
        r += ' x0=['+''.join(str(v) for v in self.x0) + ']' if self.x0 is not None else ''
        return r


    def run(self, circ, sweep_type='LINEAR', guess=True, x0=None, outfile="stdout"):
        
        logging.info("Starting DC sweep...")
        source_label = self.src.upper()
        
        points = int((self.stop - self.start) / self.step)
        sweep_type = sweep_type.upper()[:3]
        
        if sweep_type == 'LOG' and self.stop - self.start < 0:
            logging.error("dc_analysis(): DC analysis has log sweeping and negative stepping.")
            raise ValueError
        if (self.stop - self.start) * self.step < 0:
            logging.error("Unbounded stepping in DC analysis.")
            raise ValueError
        
        if sweep_type == 'LOG':
            dcs = np.logspace(int(self.start), np.log(int(self.stop)), num=int(points), endpoint=True)
        elif sweep_type == 'LIN' or sweep_type is None:
            dcs = np.linspace(int(self.start), int(self.stop), num=int(points), endpoint=True)

        if source_label[0] != ('V' or 'I'):
            logging.error("Sweeping is possible only with voltage and current sources.")
            raise ValueError(f"Source is type: {source_label[0]}")
          
        self.src = None
        for elem in [src for src in circ if isinstance(src, (components.sources.V, components.sources.I))]:
            identifier = f"{elem.name.upper()}{elem.part_id}"
            if identifier == source_label:
                self.src = elem
                logging.debug("dc_analysis(): Source found!")
                break
            logging.error("dc_analysis(): Specified source was not found")
            raise ValueError("dc_analysis(): source {self.src} was not found")
        
        # store this value to reassign later
        val_ = self.src.dc_value
         
        M_size = circ.M0.shape[0] - 1
        x = self._format_estimate(x0, M_size)
        logging.info("dc_analysis(): DC analysis starting...")
        sol = results.Solution(circ, None, 'DC', extra_header=source_label)
        # sweep setup
        solved = False
        for i, sweep_value in enumerate(dcs):
            self.src.dc_value = sweep_value
            # regenerate the matrices with new sweep value
            _ = circ.gen_matrices()
            # now call an operating point analysis
            x = op_analysis(circ, x0=x)
            if x is None:
                logging.warning("dc_analysis(): Coudn't compute \
                                operating point for {sweep_value}. \
                                    Skipping...")
                # skip
                continue
            x = np.array([float(value[0]) for value in x.values()])
            
            
            row = [sweep_value]
            row.extend(x)
            sol.write_data(row)
            # only flag as solved if loop doesn't skip any values
            solved = True            
        
        logging.info("dc_analysis(): Finished DC analysis")
        if not solved:
            logging.error("dc_analysis(): Couldn't solve for values in DC sweep")
            sol.close()
            return None
        
        sol.close()
        # ensure that DC source retains initial value
        self.src.dc_value = val_
        
        return sol.as_dict()

    def _format_estimate(self, x0, dim):
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
