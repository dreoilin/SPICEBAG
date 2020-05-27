from .Component import Component

class CurrentDefinedComponent(Component):
    """
    Base class for current defined components:
    - R
    - C
    - G cccs
    - I independent current source
    """

    def __init__(self, line):
        super().__init__(line)
        self.part_id=str(self.tokens[0])

