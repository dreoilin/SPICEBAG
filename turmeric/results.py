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
        if extra_header is not None:
            self.headers = [extra_header]
        else:
            self.headers = []
        # set circuit title as filename if not specified
        if filename is None:
            self.filename = opdir / re.sub(' ','_',f"{circ.title}.{sol_type}".strip())
        else:
            self.filename = opdir / filename
        # we have reduced MNA
        NNODES = circ.get_nodes_number() -1
        
        for i in range(NNODES):
            header = f"V({str(circ.nodes_dict[i+1])})".upper()
            self.headers.append(header)
        for elem in circ:
            if isinstance(elem, VoltageDefinedComponent):
                header=f"I({elem.part_id.upper()})"
                self.headers.append(header)
        # setup file 
        self._setup_file()
        logging.info(f'Using results file {self.filename}')
            
    def _setup_file(self):
        self.file = open(f"{self.filename}", 'w+')
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
        
        with open(f"{self.filename}", 'r') as csvfile:
            lines = csvfile.readlines()
        # set up dict keys

        headers = lines[0].rstrip().split(',')
        nrows = len(lines)

        linelist = [x.rstrip().split(',') for x in lines[1:nrows+1]]
        data = {keyVal:np.array([v_type(x[idx]) for x in linelist if len(x)==len(headers)]) for idx,keyVal in enumerate(headers)} 
        
        return data
        
