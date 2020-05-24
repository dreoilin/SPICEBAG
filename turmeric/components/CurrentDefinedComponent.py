from .Component import Component

class CurrentDefinedComponent(Component):
    """
    Base class for current defined components:
    - Resistor
    - Capacitor
    - G cccs
    - I independent current source
    """

    def __init__(self, part_id, value):
        self.part_id = part_id
        self._value = value
        self._g = 1./value

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
