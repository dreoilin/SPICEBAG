
class Wire(object):
    __tag__ = 'wire'

    def __init__(self, canvas, lineSegmentIDs = [], controlpoints = [], node = None ):
        self.canvas = canvas
        self.__lineSegmentIDs = lineSegmentIDs
        self.__controlpoints = controlpoints
        self.node = self.canvas.nextNode if node is None else node
        self.__graphicalnodes = []

        self.tag = str(self.canvas.wireCount)
        self.canvas.wireCount += 1

    def addGNode(self, p):
        self.__graphicalnodes.append(p)

    def addControlpoint(self, cp):
        self.__controlpoints.append(cp)

    def __str__(self):
        s = F"<WIRE node `{self.node}' , tag `{self.tag}' , cps `{self.__controlpoints}', lsIDs `{self.__lineSegmentIDs}' , gnodes `{self.__graphicalnodes}'>"
        return s
