"""
Tokens that appear in a netlist line
"""
from abc import ABC, abstractmethod
import re

def rex(objs):
    """
    Helper method to return regex representation of object, e.g. netlist tokens
    """
    if not hasattr(objs, '__len__'):
        return objs.__re__
    else:
        return "".join([o.__re__ for o in objs])
si = {
    "f" : 1e-15,
    "p" : 1e-12,
    "n" : 1e-09,
    "u" : 1e-06,
    "m" : 1e-03,
    ""  : 1e+00,
    "k" : 1e+03,
    "meg" : 1e+06,
    "g" : 1e+09,
    "t" : 1e+12
}

class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)

class NetlistToken(ABC):
    def __init__(self, val):
        self._value = val

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @classproperty
    @abstractmethod
    def __re__(cls):
        pass


class Label(NetlistToken):
    def __init__(self,val):
        super().__init__(val)

    def __str__(self):
        return str(self.value)

    @classproperty
    def __re__(cls):
        return r"([^ ]+)"

class Model(Label):
    """
    To use in net_objs, call classmethod with list of models as parameter
    """
    def __init__(self, val):
        super().__init__(val)
        if self.value.lower() not in [i.lower() for i in self.models.keys()]:
            raise ValueError("Model {self.value} not found in this netlist.")
        self.value = self.models[self.value]

    @classmethod
    def defined(cls, models):
        cls.models = models
        return cls

class Node(NetlistToken):
    def __init__(self,val):
        super().__init__(val)
        self.__name = str(self.value)
        self.__eid = None

    @property
    def eid(self):
        return self.__eid

    @eid.setter
    def eid(self, newid):
        self.__eid = int(newid)

    @property
    def name(self):
        return self.__name
   
    @name.setter
    def name(self, newlabel):
        self.__name = str(newlabel)

    def __int__(self): # Change to return id
        return self.eid

    def __str__(self): # Change to return display name
        return self.name

    @classproperty
    def __re__(self):
        return r"([^ ]+)"

class Value(NetlistToken):
    def __init__(self, val):
        r = r"^(?: *)([\d\.\-\+]+)(meg|[fpnumkgt])?$"
        m = re.search(r,val)
        g = m.groups()
        self.__order = si[g[1]] if g[1] is not None else 1.0
        super().__init__(float(g[0]) * self.__order)

    @classproperty
    def __re__(cls):
        return r"([\d\.\-\+]+(?:meg|[fpnumkgt])?)"

    def __float__(self):
        return float(self.value)
    def __str__(self):
        prefix = next(k for k,v in si.items() if v == self.__order)
        return str(self.value / self.__order)+prefix

class ParamDict(NetlistToken):
    """
    Place in net_objs to return a dictionary of parsed parameter=value pairs.

    Use ParamDict.allowed_params method to construct a class in the parsed component's
        net_objs list that will add the parsed parameters directly to the parsed component
        as attributes.
    This will still return the dictionary of parsed parameter=value pairs.
    """
    def __init__(self, val):
        r = '([^ \n]+=[^ \n]+)'
        m = re.findall(r,val) if val else None
        d = {}
        if m is not None:
            for g in m:
                p = KVParam(g)
                if p.key.lower() in d:
                    if isinstance(d[p.key.lower()],list):
                        d[p.key.lower()].append(p.value)
                    else:
                        l = [d[p.key.lower()]]
                        l.append(p.value)
                        d[p.key.lower()] = l
                else:
                    d.update({p.key.lower() : p.value})
        allowed = '_'+type(self).__name__+'__allowed_params'
        component = '_'+type(self).__name__+'__component'
        if hasattr(self, allowed) and hasattr(self, component):
            for param, desc in getattr(self, allowed).items():
                if param.lower() in d:
                    setattr(getattr(self,component),param,desc['type'](d[param]))
                elif desc['default'] is not None:
                    setattr(getattr(self,component),param,desc['type'](desc['default']))
                else:
                    raise ValueError(f'Missing non-default parameter {param} for {self.name} component')
        super().__init__(d)

    @classmethod
    def allowed_params(cls, component, paramset, optional=False):
        """
        paramset of the form: { 'param_name' : { 'type' : type_function_to_set_value, 'default' : [None|value]}}
        If a parameter is given a default, it will be treated as optional
        
        parameters will be added to component
        """
        cls.__component = component
        cls.__allowed_params = paramset
        cls.__optional = optional
        return cls

    @classproperty
    def __re__(cls):
        r = r"((?:(?: *)[^ \n]+=[^ \n]+)+)"
        if hasattr(cls, '_'+cls.__name__+'__optional'):
            r = f'?{r}?' if getattr(cls, '_'+cls.__name__+'__optional') else ''
        return r

class KVParam(NetlistToken):
    def __init__(self, val):
        r = r"([^ ]+)=([^ ]+)"
        m = re.search(r,val)
        g = m.groups()
        self.key = g[0]
        super().__init__(g[1])

    @classproperty
    def __re__(cls):
        return r"([^ \n]+=[^ \n]+)"

class NoLabel(NetlistToken):
    """
    Blank spacer token, used to account for directives, etc.
    """
 
    # TODO: verify needed when directive parsing completed
    def __init__(self, val):
        super().__init__(val)

    @classproperty
    def __re__(cls):
        return r"()"

class EqualsParam(NetlistToken):
    def __init__(self,val):
        super().__init__(val)
        if val is not None:
            setattr(self.__parent, self.__name, val)

    @classmethod
    def __set_validated(cls, obj, var_name, value, value_validator):
        """
        Set new attribute value after checking it with validator function
        """
        if not value_validator(value):
            raise ValueError(f"Value {value} is invalid for the element {obj.name}")
        else:
            setattr(obj,var_name,value)

    @classmethod
    def __get_enum_checker(cls, enum):
        if enum is None:
            return
        return lambda val: True if val in enum else False

    def __str__(self):
        return str(self.value)
 
    # TODO add function to set the format of the value (i.e. pass in float(), str(), etc.)
    @classmethod
    def defined(cls, name, parent, default = None, value_enum = None, is_label = False, value_validator = None, docstr = None):
        """
        Return class with attributes parameterised to specific values
        ``name'' - name of parameter, i.e. the key
        ``parent'' - will have parameter name added as attribute
        ``optional'' - whether or not this parameter is optional. Not implemented.
        Use only one of the following:
            ``value_enum'' - enumeration of possible values for the parameter. Used in regex generation.
            ``label'' - whether or not this parameter's value follows the Label class' regex. Not implemented.
            ``value_validator'' - of the form lambda v: is_v_valid? Checked on assignment (in setter).
                            Value is presumed to be of the form specified in the `Value' class, so Value regex used.
        """
        def newInit(obj, val):
            super().__init__(val)
            obj.__parent = parent
            obj.__name = str(name)
            obj.__default = default
            # TODO Only one of the following should be non-none or true
            obj.__value_enum = list(value_enum) if value_enum is not None else None
            obj.__is_label = bool(is_label)
            obj.__value_validator = value_validator
            print(f"Defining parameter class `{name}' on `{type(parent).__name__}' with default {default}, value_enum {value_enum}, is_label {is_label} and validator function {value_validator}")
            priv_var_name = f"__{name}"
            if not hasattr(parent, name):
                getvar = lambda obj: getattr(obj, priv_var_name)
                setvar = lambda obj, v: setattr(obj, priv_var_name, v)
                delvar = None
                doc    = docstr
                # Create private variable for setting and getting
                setattr(obj.__parent, priv_var_name, obj.__default)
                if obj.__value_enum is not None:
                    # TODO add this to the setter of the property
                    #              Add what?
                    setvar = lambda obj, v: cls.__set_validated(obj, priv_var_name, v, cls.__get_enum_checker(value_enum))
                if obj.__value_validator is not None:
                    setvar = lambda obj, v: cls.__set_validated(obj, priv_var_name, v, value_validator)

                prop = property(getvar,setvar,delvar,doc)
                setattr(obj.__parent.__class__, obj.__name, prop)
            if val is not None:
                setattr(obj.__parent, obj.__name, val)
                # ============ END OF NEWINIT =============

        # SETUP PARAMETER'S REGEX
        r = f"(?:{name}=)" # SPC STAR is a hack FIXME
        # If has a default, make previous spacing and prefix optional
        r = f"?{r}?" if default is not None else r

        if value_enum is not None:
            # Value is a string with a set of values
            r += "(" + "|".join(value_enum)  + ")"
        elif is_label is True:
            # Value is a label and should follow Label's regex
            r += rex(Label)
        elif value_validator is not None:
            # Value is numeric and should follow Value's regex
            r += rex(Value)
        else:
            # Default to a Value regex
            r += rex(Value)

        # If has a default, make value regex optional
        if default is not None:
            r += "?"
        #print(f"RE of {type(parent).__name__}.{name} : `{r}'")

        return type(f"{name}EqualsParam", (EqualsParam,) , {
            '__init__' : newInit,
            '__re__' : r
            })

    @classproperty
    def __re__(cls):
        return cls.__re
