from .Component import Component

class CurrentDefinedComponent(Component):
    """
    Base class for current defined components:
    - R
    - C
    - G cccs
    - I independent current source
    """

    # The below is "generalised" from R.py and might only be specific to a resistor
    def __init__(self, line):
        super().__init__(line)
        self.part_id=str(self.tokens[0])
        self._value =float(self.tokens[3])
        self._g = 1./self._value

    @property
    def g(self, v=0, time=0):
        return self._g

    @g.setter
    def g(self, g):
        self._g = g
        self._value = 1./g

    @property
    def value(self, v=0, time=0):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._g = 1./value

    def i(self, v, time=0):
        return 0
