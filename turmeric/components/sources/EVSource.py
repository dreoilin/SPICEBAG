from ..VoltageDefinedComponent import VoltageDefinedComponent
class EVSource(VoltageDefinedComponent):
    """Linear voltage-controlled voltage source

    .. image:: images/elem/vcvs.svg

    The source port is an open circuit, the destination port is an ideal
    voltage source.

    Mathematically, it is equivalent to the following:

    .. math::

        \\left\\{
        \\begin{array}{ll}
            I_s = 0\\\\
            Vn_1 - Vn_2 = \\alpha * (Vsn_1 - Vsn_2)
        \\end{array}
        \\right.

    Where :math:`I_s` is the current at the source port and the remaining
    symbols are explained in the Parameters section below.

    **Parameters:**

    n1 : int
        *Internal* node to be connected to the anode of the output port.
    n2 : int
        *Internal* node to be connected to the cathode of the output port.
    value : float
        Proportionality constant :math:`\\alpha` between the voltages.
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

    def stamp(self, M0, ZDC0, ZAC0, D0, ZT0, time):
        (M0, ZDC0, ZAC0, D0, ZT0) = super().stamp(M0, ZDC0, ZAC0, D0, ZT0)
        M0[-1, elem.sn1] = -float(elem.alpha)
        M0[-1, elem.sn2] =  float(elem.alpha)
        return (M0, ZDC0, ZAC0, D0, ZT0) 

    def __repr__(self):
        """
        E<string> n+ n- ns+ ns- <value>
        """
        return f"E{self.part_id} {self.n1} {self.n2} {self.sn1} {self.sn2} {self.alpha}"

