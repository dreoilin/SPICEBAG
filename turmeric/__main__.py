import sys
import logging
from optparse import OptionParser
from pathlib import Path

from . import turmeric, settings
from .__version__ import __version__

def _cli():
    usage = f"usage: \t%prog [settings] <filename>\n\n"\
            f"filename - netlist of circuit to simulate.\n\n"\
            f"Welcome to Turmeric, version {__version__}\n"
    parser = OptionParser(usage, version="%prog " + __version__)

    parser.add_option("-v", "--verbose", action="store_true",
            dest="verbose", default=False, help="Verbose output")
    parser.add_option("-o", "--outprefix", action="store", type="string",
                      dest="outprefix", default=settings.outprefix, help=f"Prefix to use for generated files. Defaults to `{settings.outprefix}'.")
    (opt, remaning_args) = parser.parse_args()

    if not len(remaning_args) == 1:
        print("Usage: python -m turmeric [settings] <filename>\npython -m turmeric -h for help")
        sys.exit(1)

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s : %(threadName)s : %(name)s : %(levelname)s : %(message)s')
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    if (opt.verbose):
        sh.setLevel(logging.INFO)
    else:
        sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)

    lfh = logging.FileHandler(f'{Path(settings.output_directory)/opt.outprefix}.log',mode='w',encoding='utf8')
    lfh.setLevel(logging.DEBUG)
    lfh.setFormatter(formatter)
    logger.addHandler(lfh)
    logger.addHandler(sh)

    turmeric.main(filename=remaning_args[0],outprefix=opt.outprefix)

    sys.exit(0)

if __name__ == "__main__":
    _cli()
