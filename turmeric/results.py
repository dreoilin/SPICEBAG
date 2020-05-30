import numpy as np
import csv
import logging
import re
from pathlib import Path
from turmeric.components import VoltageDefinedComponent
from . import settings
from turmeric.analyses.Analysis import analyses_vtypes

class Solution(object):
    def __init__(self, circ=None, filename=None, sol_type="", extra_header=None):
        self.sol_type = str(sol_type)
        if sol_type not in analyses_vtypes.keys():
            logging.warning(f'Solution type of {sol_type} will not be available in TISE')
        if extra_header is not None:
            self.headers = [extra_header]
        else:
            self.headers = []

        opdir = Path(settings.output_directory)
        if not opdir.is_dir():
            opdir.mkdir(exist_ok=True, parents=True)
        if filename is None:
            # set circuit title as filename if not specified
            #self.filepath = opdir / re.sub(' ','_',f"{circ.title}.{sol_type}".strip())
            self.filepath = opdir / f'{settings.outprefix}.{self.sol_type}'
        else:
            self.filepath = opdir / filename 
        logging.info(f'Using results file {self.filepath}')
        
        if circ is not None:
            # we have reduced MNA
            NNODES = circ.nnodes -1
            for i in range(NNODES):
                header = f"V({str(circ.nodes_dict[i+1])})".upper()
                self.headers.append(header)
            for elem in circ:
                if isinstance(elem, VoltageDefinedComponent):
                    header=f"I({elem.name.upper()}{elem.part_id})"
                    self.headers.append(header)
            # setup file 
            self._setup_file(mode='w')
            
    def _setup_file(self,mode):
        if mode in ['w','w+']:
            self.file = self.filepath.open(mode=mode)
            self.writer = csv.writer(self.file, delimiter=',')
            self.writer.writerow(self.headers)

    
    def write_data(self, x):
        if len(x) != len(self.headers):
            logging.error("Solution array is incorrect size")
            raise ValueError

        self.writer.writerow(x)
        
    def close(self):
        self.file.close()

    def as_dict(self, v_type=float):
        
        with self.filepath.open('r',newline='') as csvfile:
            lines = csvfile.readlines()
        # set up dict keys

        headers = lines[0].rstrip().split(',')
        nrows = len(lines)

        linelist = [x.rstrip().split(',') for x in lines[1:nrows+1]]
        data = {keyVal:np.array([v_type(x[idx]) for x in linelist if len(x)==len(headers)]) for idx,keyVal in enumerate(headers)} 
        
        return (self.sol_type, data)
        
