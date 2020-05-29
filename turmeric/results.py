import numpy as np
import csv
import logging
import re
from pathlib import Path
from turmeric.components import VoltageDefinedComponent
from . import settings

opdir = Path(settings.output_directory)

class Solution(object):
    
    def __init__(self, circ, filename=None, sol_type="", extra_header=None):
        self.sol_type = sol_type
        if extra_header is not None:
            self.headers = [extra_header]
        else:
            self.headers = []

        if not opdir.is_dir():
            opdir.mkdir(exist_ok=True, parents=True)
        if filename is None:
        # set circuit title as filename if not specified
            self.filepath = opdir / re.sub(' ','_',f"{circ.title}.{sol_type}".strip())
        else:
            self.filepath = opdir / filename
        # we have reduced MNA
        NNODES = circ.get_nodes_number() -1
        for i in range(NNODES):
            header = f"V({str(circ.nodes_dict[i+1])})".upper()
            self.headers.append(header)
        for elem in circ:
            if isinstance(elem, VoltageDefinedComponent):
                header=f"I({elem.name.upper()}{elem.part_id})"
                self.headers.append(header)
        # setup file 
        self._setup_file()
        logging.info(f'Using results file {self.filepath}')
            
    def _setup_file(self):
        self.file = self.filepath.open('w')
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
        
        with self.filepath.open('r') as csvfile:
            lines = csvfile.readlines()
        # set up dict keys

        headers = lines[0].rstrip().split(',')
        nrows = len(lines)

        linelist = [x.rstrip().split(',') for x in lines[1:nrows+1]]
        data = {keyVal:np.array([v_type(x[idx]) for x in linelist if len(x)==len(headers)]) for idx,keyVal in enumerate(headers)} 
        
        return (self.sol_type, data)
        
