from ..Component import Component
class FISource(Component):
    """
    CCCS
    """
    def __init__(self, part_id, n1, n2, value, source_id):
        self.part_id = part_id
        self.n1 = n1
        self.n2 = n2
        self.source_id = source_id
        self.alpha = value
        self.is_nonlinear = False
        self.is_symbolic = True

    def __repr__(self):
        return f"F{self.part_id} {self.n1} {self.n2} {self.source_id} {self.alpha}"

