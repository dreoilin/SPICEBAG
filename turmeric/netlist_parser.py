#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 11:23:45 2020

@author: cian

"""

import sys
import math
import copy
import os
import logging

from . import circuit
from . import components
from . import diode
from . import printing

# analyses syntax
from .dc import specs as dc_spec
from .ac import specs as ac_spec
from .transient import specs as tran_spec
from .time_functions import time_fun_specs
from .time_functions import sin, pulse, exp, sffm, am


specs = {}
for i in dc_spec, ac_spec, tran_spec:
    specs.update(i)

time_functions = {}
for i in sin, pulse, exp, sffm, am:
    time_functions.update({i.__name__:i})

class NetlistParseError(Exception):
    """Netlist parsing exception."""
    pass


def parse_models(lines):
    models = {}
    for line, line_n in lines:
        tokens = line.replace("(", "").replace(")", "").split()
        if len(tokens) < 3:
            raise NetlistParseError("parse_models(): syntax error in model declaration on line " + str(line_n) +
                                    ".\n\t" + line)
        model_label = tokens[2]
        model_type = tokens[1]
        model_parameters = {}
        for index in range(3, len(tokens)):
            if tokens[index][0] == "*":
                break
            (label, value) = parse_param_value_from_string(tokens[index])
            model_parameters.update({label.upper(): value})
        if model_type == "diode" or model_type == 'd':
            model_parameters.update({'name': model_label})
            model_iter = diode.diode_model(**model_parameters)
        else:
            raise NetlistParseError("parse_models(): Unknown model (" +
                                    model_type + ") on line " + str(line_n) +
                                    ".\n\t" + line,)
        models.update({model_label: model_iter})
    return models


def digest_raw_netlist(filename):
    logging.info(f"Processing netlist `{filename}'")
    directives = []
    models = []
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
                    model_directives.append((line, i+1))
                else:
                    directives.append((line, i+1))
                continue
            
            net_lines.append((line, i + 1))
    models = parse_models(model_directives)
    analyses = parse_analysis(directives)
    logging.info(f"Finished processing `{filename}'")
    
    return (title, analyses, models, net_lines)


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
    #circ.generate_M0_and_ZDC0()
    circ.gen_matrices()

    return (circ, analyses)


def main_netlist_parser(circ, netlist_lines, models):
    elements = []
    parse_function = {
        'c': lambda line: components.C(line, circ),
        'd': lambda line: parse_elem_diode(line, circ, models),
        'e': lambda line: parse_elem_vcvs(line, circ),
        'f': lambda line: parse_elem_cccs(line, circ),
        'g': lambda line: parse_elem_vccs(line, circ),
        'h': lambda line: components.sources.H(line, circ),
        'i': lambda line: parse_elem_isource(line, circ),
        'l': lambda line: components.L(line, circ),
        'r': lambda line: components.R(line, circ),
        'v': lambda line: components.sources.V(line,circ)
    }
    try:
        for line, line_n in netlist_lines:
            try:
                e = parse_function[line[0]](line)
                # TODO: remove once all elements parsed via inheritance
                elements.append(e if type(e) is not list else e[0])
            except KeyError:
                raise NetlistParseError(f"Cannot parse {line[0]} element")
    except NetlistParseError as npe:
        (msg,) = npe.args
        if len(msg):
            printing.print_general_error(msg)
        printing.print_parse_error(line_n, line)
        raise NetlistParseError(msg)

    return elements


def parse_elem_isource(line, circ):
    line_elements = line.split()
    if len(line_elements) < 3:
        raise NetlistParseError("parse_elem_isource(): malformed line")

    dc_value = None
    iac = None
    function = None

    index = 3
    while True:
        if index == len(line_elements):
            break
        if line_elements[index][0] == '*':
            break

        (label, value) = parse_param_value_from_string(line_elements[index])

        if label == 'type':
            if value == 'idc':
                param_number = 0
            elif value == 'iac':
                param_number = 0
            elif value == 'pulse':
                param_number = 7
            elif value == 'exp':
                param_number = 6
            elif value == 'sin':
                param_number = 5
            elif value == 'sffm':
                param_number = 5
            elif value == 'am':
                param_number = 5
            else:
                raise NetlistParseError("parse_elem_isource(): unknown signal type.")
            if param_number and function is None:
                function = parse_time_function(value,
                                               line_elements[index + 1:
                                                             index + param_number + 1],
                                               "current")
                index = index + param_number
            elif function is not None:
                raise NetlistParseError("parse_elem_isource(): only a time function can be defined.")
        elif label == 'idc':
            dc_value = convert_units(value)
        elif label == 'iac':
            iac = convert_units(value)
        else:
            raise NetlistParseError("parse_elem_isource(): unknown type "+label)
        index = index + 1

    if dc_value == None and function == None:
        raise NetlistParseError("parse_elem_isource(): neither idc nor a time function are defined.")

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)

    elem = components.sources.ISource(part_id=line_elements[0], n1=n1, n2=n2,
                           dc_value=dc_value, ac_value=iac)

    if function is not None:
        elem.is_timedependent = True
        elem._time_function = function

    return [elem]


def parse_elem_diode(line, circ, models=None):
    
    Area = None
    T = None
    ic = None
    off = False

    line_elements = line.split()
    if len(line_elements) < 4:
        raise NetlistParseError("")

    model_label = line_elements[3]

    for index in range(4, len(line_elements)):
        if line_elements[index][0] == '*':
            break
        param, value = parse_param_value_from_string(line_elements[index])

        value = convert_units(value)
        if param == "area":
            Area = value
        elif param == "t":
            T = value
        elif param == "ic":
            ic = value
        elif param == "off":
            if not len(value):
                off = True
            else:
                off = convert_boolean(value)
        else:
            raise NetlistParseError("parse_elem_diode(): unknown parameter " + param)

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)

    if model_label not in models:
        raise NetlistParseError("parse_elem_diode(): Unknown model id: " + model_label)
    elem = diode.diode(part_id=line_elements[0], n1=n1, n2=n2, model=models[
                       model_label], AREA=Area, ic=ic, off=off)
    return [elem]


def parse_elem_vcvs(line, circ):
    
    line_elements = line.split()
    if len(line_elements) < 6 or (len(line_elements) > 6 and not line_elements[6][0] == "*"):
        raise NetlistParseError("")

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    ext_sn1 = line_elements[3]
    ext_sn2 = line_elements[4]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)
    sn1 = circ.add_node(ext_sn1)
    sn2 = circ.add_node(ext_sn2)

    elem = components.sources.EVSource(part_id=line_elements[0], n1=n1, n2=n2, sn1=sn1,
                            sn2=sn2, value=convert_units(line_elements[5]))

    return [elem]


def parse_elem_ccvs(line, circ):
    
    line_elements = line.split()
    if len(line_elements) < 5 or (len(line_elements) > 5 and not
                                  line_elements[5][0] == "*"):
        raise NetlistParseError("")

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)

    elem = components.sources.H(part_id=line_elements[0], n1=n1, n2=n2,
                            source_id=line_elements[3],
                            value=convert_units(line_elements[4]))

    return [elem]


def parse_elem_vccs(line, circ):
    
    line_elements = line.split()
    if len(line_elements) < 6 or (len(line_elements) > 6
       and not line_elements[6][0] == "*"):
        raise NetlistParseError("")

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    ext_sn1 = line_elements[3]
    ext_sn2 = line_elements[4]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)
    sn1 = circ.add_node(ext_sn1)
    sn2 = circ.add_node(ext_sn2)

    elem = components.sources.GISource(part_id=line_elements[0], n1=n1, n2=n2, sn1=sn1,
                            sn2=sn2, value=convert_units(line_elements[5]))

    return [elem]


def parse_elem_cccs(line, circ):
    

    line_elements = line.split()
    if len(line_elements) < 5 or (len(line_elements) > 5
       and not line_elements[5][0] == "*"):
        raise NetlistParseError("")

    ext_n1 = line_elements[1]
    ext_n2 = line_elements[2]
    source_id = line_elements[3]
    n1 = circ.add_node(ext_n1)
    n2 = circ.add_node(ext_n2)

    elem = components.sources.FISource(part_id=line_elements[0], n1=n1, n2=n2,
                            source_id=source_id,
                            value=convert_units(line_elements[4]))

    return [elem]


def parse_time_function(ftype, line_elements, stype):
    
    if not ftype in time_fun_specs:
        raise NetlistParseError("Unknown time function: %s" % ftype)
    prot_params = list(copy.deepcopy(time_fun_specs[ftype]['tokens']))

    fun_params = {}
    for i in range(len(line_elements)):
        token = line_elements[i]
        if token[0] == "*":
            break
        if is_valid_value_param_string(token):
            (label, value) = token.split('=')
        else:
            label, value = None, token
        assigned = False
        for t in prot_params:
            if (label is None and t['pos'] == i) or label == t['label']:
                fun_params.update({t['dest']: convert(value, t['type'])})
                assigned = True
                break
        if assigned:
            prot_params.pop(prot_params.index(t))
            continue
        else:
            raise NetlistParseError("Unknown .%s parameter: pos %d (%s=)%s" % \
                                     (ftype.upper(), i, label, value))

    missing = []
    for t in prot_params:
        if t['needed']:
            missing.append(t['label'])
    if len(missing):
        raise NetlistParseError("%s: required parameters are missing: %s" % (ftype, " ".join(line_elements)))
    # load defaults for unsupplied parameters
    for t in prot_params:
        fun_params.update({t['dest']: t['default']})

    fun = time_functions[ftype](**fun_params)
    fun._type = "V" * \
        (stype.lower() == "voltage") + "I" * (stype.lower() == "current")
    return fun


def convert_units(string_value):

    if type(string_value) is float:
        return string_value  # not actually a string!
    if not len(string_value):
        raise NetlistParseError("")

    index = 0
    string_value = string_value.strip().upper()
    while(True):
        if len(string_value) == index:
            break
        if not (string_value[index].isdigit() or string_value[index] == "." or
                string_value[index] == "+" or string_value[index] == "-" or
                string_value[index] == "E"):
            break
        index = index + 1
    if index == 0:
        # print string_value
        raise ValueError("Unable to parse value: %s" % string_value)
        # return 0
    numeric_value = float(string_value[:index])
    multiplier = string_value[index:]
    if len(multiplier) == 0:
        pass # return numeric_value
    elif multiplier == "T":
        numeric_value = numeric_value * 1e12
    elif multiplier == "G":
        numeric_value = numeric_value * 1e9
    elif multiplier == "K":
        numeric_value = numeric_value * 1e3
    elif multiplier == "M":
        numeric_value = numeric_value * 1e-3
    elif multiplier == "U":
        numeric_value = numeric_value * 1e-6
    elif multiplier == "N":
        numeric_value = numeric_value * 1e-9
    elif multiplier == "P":
        numeric_value = numeric_value * 1e-12
    elif multiplier == "F":
        numeric_value = numeric_value * 1e-15
    elif multiplier == "MEG":
        numeric_value = numeric_value * 1e6
    elif multiplier == "MIL":
        numeric_value = numeric_value * 25.4e-6
    else:
        raise ValueError("Unknown multiplier %s" % multiplier)
    return numeric_value


def parse_ics(directives):
    ics = []
    for line, line_n in directives:
        if line[0] != '.':
            continue
        if line[:3] == '.ic':
            ics += [parse_ic_directive(line)]
    return ics


def parse_analysis(directives):
    
    an = []
    for line, line_n in directives:
        if line[0] != '.' or line[:3] == '.ic':
            continue
        line_elements = line.split()
        an += [parse_single_analysis(line)]
    return an


def parse_temp_directive(line):
    
    line_elements = line.split()
    for token in line_elements[1:]:
        if token[0] == "*":
            break
        value = convert_units(token)

    return {"type": "temp", "temp": value}


def parse_single_analysis(line):
    
    line_elements = line.split()
    an_type = line_elements[0].replace(".", "").lower()
    if not an_type in specs:
        raise NetlistParseError("Unknown directive: %s" % an_type)
    params = list(copy.deepcopy(specs[an_type]['tokens']))

    an = {'type': an_type}
    for i in range(len(line_elements[1:])):
        token = line_elements[i + 1]
        if token[0] == "*":
            break
        if is_valid_value_param_string(token):
            (label, value) = token.split('=')
        else:
            label, value = None, token
        assigned = False
        for t in params:
            if (label is None and t['pos'] == i) or label == t['label']:
                an.update({t['dest']: convert(value, t['type'])})
                assigned = True
                break
        if assigned:
            params.pop(params.index(t))
            continue
        else:
            raise NetlistParseError("Unknown .%s parameter: pos %d (%s=)%s" % \
                                     (an_type.upper(), i, label, value))

    missing = []
    for t in params:
        if t['needed']:
            missing.append(t['label'])
    if len(missing):
        raise NetlistParseError("Required parameters are missing: %s" %
                                (" ".join(line_elements)))

    for t in params:
        an.update({t['dest']: t['default']})

    if an['type'] == 'tran':
        uic = int(an.pop('uic'))
        if uic == 0:
            an['x0'] = None
        elif uic == 1:
            an['x0'] = 'op'
        elif uic == 2:
            an['x0'] = 'op+ic'
        elif uic == 3:
            pass  # already set by ic_label
        else:
            raise NetlistParseError("Unknown UIC value: %d" % uic)

    return an


def is_valid_value_param_string(astr):
    
    work_astr = astr.strip()
    if work_astr.count("=") == 1:
        ret_value = True
    else:
        ret_value = False
    return ret_value


def convert(astr, rtype, raise_exception=False):
    
    if rtype == float:
        try:
            ret = convert_units(astr)
        except ValueError as msg:
            if raise_exception:
                raise ValueError(msg)
            else:
                ret = astr
    elif rtype == str:
        ret = astr
    elif rtype == bool:
        ret = convert_boolean(astr)
    elif raise_exception:
        raise ValueError("Unknown type %s" % rtype)
    else:
        ret = astr
    return ret


def parse_param_value_from_string(astr, rtype=float, raise_exception=False):
    
    if not is_valid_value_param_string(astr):
        return (astr, "")
    p, v = astr.strip().split("=")
    v = convert(v, rtype, raise_exception=False)
    return p, v


def convert_boolean(value):
    
    if value == 'no' or value == 'false' or value == '0' or value == 0:
        return_value = False
    elif value == 'yes' or value == 'true' or value == '1' or value == 1:
        return_value = True
    else:
        raise NetlistParseError("invalid boolean: " + value)

    return return_value


def parse_ic_directive(line):
    """Parses an ic directive and assembles a dictionary accordingly.
    """
    line_elements = line.split()
    ic_dict = {}
    name = None
    for token in line_elements[1:]:
        if token[0] == "*":
            break

        (label, value) = parse_param_value_from_string(token)
        if label == "name" and name is None:
            name = value
            continue
        # check if node actually exists, raise error
        ic_dict.update({label: convert_units(value)})

    if name is None:
        raise NetlistParseError("The 'name' parameter is missing")

    return {name: ic_dict}


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
