# Spicebag

## Setup
run `make` from the root directory.
Fortran objects will be compiled.

All requirements should be put into requirements.txt such that the command `make requirements` will install them via pip.

## GUI
`python -m turmeric.gui`

## CLI
See `turmeric/__main__.py`  
To simulate a netlist `<netlist>` and have all output files prefixed with `<prefix>`, run:  
`python -m turmeric [-o <prefix>] <netlist>`

## Module
You can import turmeric as a python module. Place the script in the root directory and use:

`from turmeric import main`

The main function returns a nicely formatted dictionary of results
