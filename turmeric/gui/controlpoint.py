
class Controlpoint(object):
    __tag__ = 'controlpoint'

    def __init__(self, component, component_cpid, position, radius=6, colour = 'green'):
        self.component = component
        self.component_cpid = component_cpid
        self.position = position
        self.radius = radius
        self.colour = colour

        # TODO replace photoimage string with component's unique identifier when added
        #self.tag = str(self.component.photoimg)+str(component_cpid)
        # Above todo not needed if cps found hierarchically
        self.tag = str(component_cpid)

        self.node = None
        self.canvas_id = None
