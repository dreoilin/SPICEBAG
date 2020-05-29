import sys
import numpy as np
import scipy as sp
import logging

from turmeric import netlist_parser
from turmeric import units
from turmeric.config import load_config
from turmeric.__version__ import __version__

def temp_directive(T): # T in celsius
    units.T = units.Kelvin(float(T))

analysis = {'temp': temp_directive}

def main(filename, outfile="out"):
    """
    filename : string
        The netlist filename.

    outfile : string, optional
        The output file's base name to which a suffix corresponding to the analysis performed will be added.
    **Returns:**
    res : dict
        A dictionary containing the computed results.
    """
    logging.info("This is turmeric %s running with:" % __version__)
    logging.info("==Python %s" % (sys.version.split('\n')[0],))
    logging.info("==Numpy %s" % (np.__version__))
    logging.info("==Scipy %s" % (sp.__version__))
    
    load_config()

    logging.info(f"Parsing netlist file `{filename}'")
    try:
        (circ, analyses) = netlist_parser.parse_network(filename)
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

def runnet(filename):
    """
    Entry point for gui
    """
    res = main(filename)
    return res
