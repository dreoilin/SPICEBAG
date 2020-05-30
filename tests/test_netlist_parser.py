import unittest
from pathlib import Path
import numpy, codecs, json

from .context import turmeric

from turmeric import parser as np

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
        for teststr, verification_str in zip(self.diode_model_strs_pass, self.diode_model_verification_strs_pass):
            #print(str(list(np.parse_models([(ms,0)]).values())[0]))
            self.assertEqual(str(list(np.parse_models([(teststr,0)]).values())[0]),verification_str)

    # TODO: test verification errors in diode model parsing

class MatrixStampingTestCase(unittest.TestCase):

    def setUp(self):
        datapath = Path('tests/data/')
        data_prefixes = ['VRD','FifthOrderLowpass']
        mattypes = ['M0', 'ZDC0']

        matfiledict = {mattype : [codecs.open(str(datapath / 'matrices' / (prefix + '.' + mattype + '.json')), 'r') for prefix in data_prefixes] for mattype in mattypes}
        self.mats = {m : [numpy.array(json.loads(f.read())) for f in matfiledict[m]] for m in matfiledict}
        [f.close() for f in [i for sublist in matfiledict.values() for i in sublist]]

        self.netlists = [str(datapath / 'netlists' / (prefix + '.net')) for prefix in data_prefixes ]
        self.genMats = {t : [getattr(np.parse_network(fn)[0],t) for fn in self.netlists] for t in mattypes}

    def test_M0_generation(self):
        for m, gm, n in zip(self.mats['M0'], self.genMats['M0'], self.netlists):
            with self.subTest(netlist=n):
                self.assertEqual(gm.tolist(), m.tolist())

    def test_ZDC0_generation(self):
        for m, gm, n in zip(self.mats['ZDC0'], self.genMats['ZDC0'], self.netlists):
            self.assertEqual(gm.tolist(), m.tolist())

