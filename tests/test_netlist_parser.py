import unittest
from .context import turmeric

from turmeric import netlist_parser as np

class FileTestCase(unittest.TestCase):

    # parse_network calls sys.exit()
    # DONE: let the exception propagate to some main file
    def test_netlist_doesnt_exist(self):
        self.assertRaises(FileNotFoundError, np.parse_network, "FileThatDoesntExist")

# testing parse_models
class ModelTestCase(unittest.TestCase):

    def setUp(self):
        self.diode_model_strs_pass = [
                '.model d d',
                '.model diode DiodeModelName',
                '.model diode DiodeModelName IS=1e-5 N=2 ISR=1 NR=3 RS=1 CJ0=1 M=0.7 VJ=0.6 FC=0.1 CP=2 TT=1 BV=2 IBV=0.01 KF=1 AF=2 FFE=2 TEMP=80.85 XTI=3 EG=1.13 TBV=7 TRS=2 TTT1=1 TTT2=2 TM1=1 TM2=2'
                ]
        self.diode_model_verification_strs_pass = [
                '.model diode d IS=1e-14 N=1 ISR=0 NR=2 RS=0 CJ0=0 M=0.5 VJ=0.7 FC=0.5 CP=0 TT=0 BV=inf IBV=0.001 KF=0 AF=1 FFE=1 TEMP=26.85 XTI=3 EG=1.11 TBV=0 TRS=0 TTT1=0 TTT2=0 TM1=0 TM2=0',
                '.model diode DiodeModelName IS=1e-14 N=1 ISR=0 NR=2 RS=0 CJ0=0 M=0.5 VJ=0.7 FC=0.5 CP=0 TT=0 BV=inf IBV=0.001 KF=0 AF=1 FFE=1 TEMP=26.85 XTI=3 EG=1.11 TBV=0 TRS=0 TTT1=0 TTT2=0 TM1=0 TM2=0',
                '.model diode DiodeModelName IS=1e-05 N=2 ISR=1 NR=3 RS=1 CJ0=1 M=0.7 VJ=0.6 FC=0.1 CP=2 TT=1 BV=2 IBV=0.01 KF=1 AF=2 FFE=2 TEMP=354 XTI=3 EG=1.13 TBV=7 TRS=2 TTT1=1 TTT2=2 TM1=1 TM2=2'
                ]

    def test_diode_model_parsing(self):
        for teststr, verification_str in zip(self.diode_model_strs, self.diode_model_verification_strs):
            #print(str(list(np.parse_models([(ms,0)]).values())[0]))
            self.assertEqual(str(list(np.parse_models([(teststr,0)]).values())[0]),verification_str)

    # TODO: test verification errors in diode model parsing
