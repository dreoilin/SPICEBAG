from .CurrentDefinedComponent import CurrentDefinedComponent

class Resistor(CurrentDefinedComponent,list):
    """A resistor.

    **Parameters:**

    part_id : string
        The unique identifier of this element. The first letter should be ``'R'``.
    n1 : int
        *Internal* node to be connected to the anode.
    n2 : int
        *Internal* node to be connected to the cathode.
    value : float
        Resistance in ohms.

     """
    #
    #             /\    /\    /\
    #     n1 o---+  \  /  \  /  \  +---o n2
    #                \/    \/    \/
    #
    def __init__(self, part_id, n1, n2, value):
        super().__init__(part_id, value)
        self.is_nonlinear = False
        self.n1 = n1
        self.n2 = n2

    @classmethod
    def from_line(cls, line, circ):
        tok = line.split()
        if len(tok) < 4 or (len(tok) > 4 and not tok[4][0] == "*"):
            raise ValueError("Malformed line: `{line}'")

        n1 = circ.add_node(tok[1])
        n2 = circ.add_node(tok[2])

        # TODO: use value types from old project
        value = float(tok[3])

        if value == 0:
            raise ValueError(f"A resistor must have a value: `{line}'")

        return [cls(part_id=tok[0], n1=n1, n2=n2, value=value)]


    def stamp(self, M, ZDC, ZAC, D):
        M[self.n1, self.n1] = M[self.n1, self.n1] + self.g
        M[self.n1, self.n2] = M[self.n1, self.n2] - self.g
        M[self.n2, self.n1] = M[self.n2, self.n1] - self.g
        M[self.n2, self.n2] = M[self.n2, self.n2] + self.g


    def get_op_info(self, ports_v):
        """Information regarding the Operating Point (OP)

        **Parameters:**

        ports_v : list of lists
            The parameter is to be set to ``[[v]]``, where ``v`` is the voltage
            applied to the resistor terminals.

        **Returns:**

        op_keys : list of strings
            The labels corresponding to the numeric values in ``op_info``.
        op_info : list of floats
            The values corresponding to ``op_keys``.
        """
        vn1n2 = float(ports_v[0][0])
        in1n2 = float(ports_v[0][0]/self.value)
        power = float(ports_v[0][0] ** 2 / self.value)
        op_keys = ['Part ID', u"R [\u2126]", "V(n1,n2) [V]", "I(n1->n2) [A]", "P [W]"]
        op_info = [self.part_id.upper(), self.value, vn1n2, in1n2, power]
        return op_keys, op_info
