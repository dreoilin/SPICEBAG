import sys
import numpy as np
import scipy as sp
import logging

from turmeric import parser,settings
from turmeric import units
from turmeric.config import load_config
from turmeric.__version__ import __version__

def temp_directive(T): # T in celsius
    units.T = units.Kelvin(float(T))

analysis = {'temp': temp_directive}

def main(filename,outprefix):
    """
    filename : string
        The netlist filename.

    **Returns:**
    res : dict
        A dictionary containing the computed results.
    """
    logging.info(f"This is turmeric {__version__} running with:")
    logging.info(f"==Python {sys.version.split()[0]}")
    logging.info(f"==Numpy {np.__version__}")
    logging.info(f"==Scipy {sp.__version__}")
    
    load_config()
    settings.outprefix = outprefix

    logging.info(f"Parsing netlist file `{filename}'")
    try:
        (circ, analyses) = parser.parse_network(filename)
    except FileNotFoundError as e:
        logging.exception(f"{e}: netlist file {filename} was not found")
        sys.exit()

    logging.info("Parsed circuit:")
    logging.info(repr(circ) + '\n' + '\n'.join(repr(m) for m in circ.models.values()))

    results = {}
    for a in analyses:
        logging.info(f"Analysis {a} running")
        an, res = a.run(circ)
        results[an] = res
        # TODO: are more than one analysis of a single type a real use case?
        #if an not in results:
        #    results[an] = [res]
        #else:
        #    results[an].append(res)
    return results
