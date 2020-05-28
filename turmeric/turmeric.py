import copy
import sys


import numpy as np
import scipy as sp
import tabulate

# analyses
from . import dc
from . import dc_sweep
from . import transient
from . import ac
from . import netlist_parser
from . import units
from . import printing

from turmeric.config import load_config

from .__version__ import __version__

import logging

def run(circ, an_list=None):
    results = {}

    an_list = copy.deepcopy(an_list)
    if type(an_list) == tuple:
        an_list = list(an_list)
    elif type(an_list) == dict:
        an_list = [an_list] # run(mycircuit, op1)

    while len(an_list):
        an_item = an_list.pop(0)
        an_type = an_item.pop('type')
        if 'x0' in an_item and isinstance(an_item['x0'], str):
            logging.warning("%s has x0 set to %s, unavailable. Using 'None'." %
                                   (an_type.upper(), an_item['x0']))
            an_item['x0'] = None
        r = analysis[an_type](circ, **an_item)
        results.update({an_type: r})
        
    return results

def set_temperature(T): # T in celsius
    units.T = units.Kelvin(float(T))

analysis = {'op': dc.op_analysis, 'dc': dc_sweep.dc_analysis,
            'tran': transient.transient_analysis, 'ac': ac.ac_analysis,
            'temp': set_temperature}


def main(filename, outfile="out"):
    """
    filename : string
        The netlist filename.

    outfile : string, optional
        The output file's base name to which a suffix corresponding to the analysis performed will be added.
    - Alternate Current (AC): ``.ac``
    - Direct Current (DC): ``.dc``
    - Operating Point (OP): ``.opinfo``
    - TRANsient (TRAN): ``.tran``

    **Returns:**

    res : dict
        A dictionary containing the computed results.
    """
    logging.info("This is turmeric %s running with:" % __version__)
    logging.info("==Python %s" % (sys.version.split('\n')[0],))
    logging.info("==Numpy %s" % (np.__version__))
    logging.info("==Scipy %s" % (sp.__version__))
    logging.info("==Tabulate %s" % (tabulate.__version__))
    
    load_config()
    from turmeric.config import options as opt
    import turmeric.options as opt2
    print(f"vea = {opt2.vea}")

    logging.info(f"Parsing netlist file `{filename}'")
    try:
        (circ, analyses) = netlist_parser.parse_network(filename)
    except FileNotFoundError as e:
        logging.exception(f"{e}: netlist file {filename} was not found")
        sys.exit()
    except IOError as e:
        # TODO: verify that parse_network can throw IOError
        logging.exception(f"{e}: ioerror on netlist file {filename}")
        sys.exit()

    logging.info("Parsed circuit:")
    logging.info(repr(circ) + '\n' + '\n'.join(repr(m) for m in circ.models.values()))

    results = {}
    for an in analyses:
        logging.info(f"Analysis {an} running")
        results.update(run(circ, [an]))

    return results

