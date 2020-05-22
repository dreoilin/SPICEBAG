import unittest
from .context import turmeric

from turmeric import netlist_parser as np

class FileTestCase(unittest.TestCase):

    # parse_network calls sys.exit()
    # TODO: let the exception propagate to some main file
    @unittest.expectedFailure
    def test_netlist_doesnt_exist(self):
        self.assertRaises(FileNotFoundError, np.parse_network, "FileThatDoesntExist")

