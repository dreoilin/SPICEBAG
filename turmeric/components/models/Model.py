from turmeric.Directive import Directive

class Model(Directive):
    def __init__(self, line):
        self.name='model'
        super().__init__(line)
