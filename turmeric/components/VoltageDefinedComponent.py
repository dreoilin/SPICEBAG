from .Component import Component

class VoltageDefinedComponent(Component):
    """
    Baseclass for voltage defined components:
    - V independent volage source
    - E vcvs
    - H ccvs
    - Inductor
    """
    
    #def __init__(self, part_id, n1, n2, dc_value, ac_value=0): # V
    #def __init__(self, part_id, n1, n2, value, sn1, sn2): # EVSource
    #def __init__(self, part_id, n1, n2, value, source_id): # HVSource
    #def __init__(self, part_id, n1, n2, value, ic=None): # Inductor

    def __init__(self, part_id, n1, n2, value):
        self.part_id = part_id
        self.value = value
        self.n1 = n1
        self.n2 = n2
