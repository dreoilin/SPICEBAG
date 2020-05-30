# Spicebag

## Setup
run `make` from the root directory.
Fortran objects will be compiled.

All requirements should be put into requirements.txt such that the command `make requirements` will install them via pip.

## CLI
See `turmeric/__main__.py`  
To simulate a netlist `<netlist>` and have all output files prefixed with `<prefix>`, run:  
`python -m turmeric [-o <prefix>] <netlist>`
