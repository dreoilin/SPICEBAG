import copy
import os
import logging

from turmeric import circuit
from turmeric import components
from turmeric import analyses


class NetlistParseError(Exception):
    """Netlist parsing exception."""
    pass


def digest_raw_netlist(filename):
    logging.info(f"Processing netlist `{filename}'")
    directives = []
    model_directives = []
    net_lines = []
    title = ""

    with open(filename, 'r') as f:
        for i, line in enumerate(f.readlines()):
            line = line.strip().lower()
 
            if i == 0:
                title = line[1:]
                continue
            if line.isspace() or line == '' or line[0] == "*":
                continue
 
            # Directives, models statements, etc.
            if line[0] == ".":
                tokens = line.split()
                if tokens[0] == '.include':
                    logging.info(f"Including `{filename}'")
                    (t, d, md, nl) = digest_raw_netlist(parse_include_directive(line, os.path.split(filename)[0]))
                    directives.extend(d)
                    models.extend(md)
                    net_lines.extend(nl)
                    if t:
                        logging.info(f"Found title `{t}' in included file. Ignoring...")
                elif tokens[0] == ".end":
                    break
                elif tokens[0] == ".model":
                    model_directives.append(line)
                else:
                    directives.append(line)
                continue
            net_lines.append(line)
    modelsmap = {
            "d" : components.models.Shockley
            }
    models = {m.model_id : m for m in [modelsmap[line.split()[1]](line) for line in model_directives]}
    directivesmap = {
        ".ac"   : analyses.AC,
        ".op"   : analyses.OP,
        ".dc"   : analyses.DC,
        ".tran" : analyses.TRAN
    }
    ans = [directivesmap[line.split()[0]](line) for line in directives]
    logging.info(f"Finished processing `{filename}'")
    return (title, ans, models, net_lines)

def parse_network(filename):
    """Parse a SPICE-like netlist

    **Returns:**

    (circuit_instance, plotting directives)
    """
    (title, analyses, models, net_lines) = digest_raw_netlist(filename)
    circ = circuit.Circuit(title=title, filename=filename)

    # PARSE CIRCUIT
    circ += main_netlist_parser(circ, net_lines, models)
    # FIXME: surely models should be assigned through the constructor
    circ.models = models
    circ.gen_matrices()

    return (circ, analyses)


def main_netlist_parser(circ, netlist_lines, models):
    elements = []
    constructor = {
        'c': lambda line: components.C(line, circ),
        'd': lambda line: components.D(line, circ, models),
        'e': lambda line: components.sources.E(line, circ),
        'g': lambda line: components.sources.G(line, circ),
        'i': lambda line: components.sources.I(line, circ),
        'l': lambda line: components.L(line, circ),
        'r': lambda line: components.R(line, circ),
        'v': lambda line: components.sources.V(line,circ)
    }
    for line in netlist_lines:
        try:
            elements.append(constructor[line[0]](line))
        except KeyError:
            raise logging.exception(f"Unknown element {line[0]} in {line}")
    return elements

def parse_temp_directive(line):
    
    from turmeric.components.tokens import Value
    line_elements = line.split()
    for token in line_elements[1:]:
        if token[0] == "*":
            break
        value = float(Value(token))

    return {"type": "temp", "temp": value}


def parse_include_directive(line, wd):
    """.include <filename> [*comments]
    """
    tokens = line.split()
    if not len(tokens) > 1 or \
            (len(tokens) > 2 and not tokens[2][0] == '*'):
        raise NetlistParseError("")

    path = tokens[1]
    if not os.path.isabs(path):
        # the user did not specify the full path.
        # the path is then assumed to be relative to the netlist location
        path = os.path.join(wd, path)

    return path
