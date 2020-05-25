from ..CurrentDefinedComponent import CurrentDefinedComponent
class GISource(CurrentDefinedComponent):

    """Linear voltage controlled current source

    .. image:: images/elem/vccs.svg

    The source port is an open circuit, the output port is an ideal current
    source:

    .. math::

        \\left\\{
        \\begin{array}{ll}
            I_s = 0\\\\
            I_o = \\alpha \\cdot (V(sn_1) - V(sn_2))
        \\end{array}
        \\right.


    Where :math:`I_s` is the current at the source port and :math:`I_o` is the
    current at the output port.
    The remaining symbols are explained in the Parameters section below.

    .. note::

        This simulator uses the passive convention: a positive current flows
        into the element through the anode and exits through the cathode.

    **Parameters:**

    n1 : int
        *Internal* node to be connected to the anode of the output port.
    n2 : int
        *Internal* node to be connected to the cathode of the output port.
    value : float
        Proportionality constant :math:`\\alpha` between the sense voltage and
        the output current, in Ampere/Volt.
    sn1 : int
        *Internal* node to be connected to the anode of the source (sensing)
        port.
    sn2 : int
        *Internal* node to be connected to the cathode of the source
        (sensing) port.

    """

    def __init__(self, part_id, n1, n2, value, sn1, sn2):
        self.part_id = part_id
        self.n1 = n1
        self.n2 = n2
        self.alpha = value
        self.sn1 = sn1
        self.sn2 = sn2
        self.is_nonlinear = False

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0):
        M0[self.n1, self.sn1] = M0[self.n1, self.sn1] + self.alpha
        M0[self.n1, self.sn2] = M0[self.n1, self.sn2] - self.alpha
        M0[self.n2, self.sn1] = M0[self.n2, self.sn1] - self.alpha
        M0[self.n2, self.sn2] = M0[self.n2, self.sn2] + self.alpha

    def __repr__(self):
        """
        G<string> n+ n- ns+ ns- <value>
        """
        return f"G{self.part_id} {self.n1} {self.n2} {self.sn1} {self.sn2} {self.alpha}"

