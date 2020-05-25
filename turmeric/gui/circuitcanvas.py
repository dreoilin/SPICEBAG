from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps

from pathlib import Path

from collections import namedtuple, defaultdict
from recordclass import recordclass

from .statusbar import Statusbar
from .mode import Modes
from .component import Component
from .controlpoint import Controlpoint
from .geometry import Point
from .wire import Wire

Size = namedtuple('Size', 'w h')
Direction = recordclass('Direction', 'n e s w')

def getNullDirection():
    return Direction(False, False, False, False)

def NOP(e=None):
    #print("NOP")
    pass

def NOP_factory():
    return defaultdict(lambda:NOP)

def bindmodefn(obj, evtstr):
    obj.bind(evtstr, obj.evalModeFn(evtstr))

class CircuitCanvas(Canvas):
    def __init__(self, master,respath=''):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        self.lineDraw = False
        self.nodes = []
        self.__nextNode = -1

        self.gridSize = Size(24,24)
        self.hitradius = 3
        self.minDrawThreshold = Point(6,6)
        self.lineDir = getNullDirection()
        self.lineIdx = 0

        self.last = {
                'lineID'    : None,
                'lineEnd'   : Point(0,0),
                'lineStart' : Point(0,0),
                'ghost'     : Point(0,0)
                }

        respath = Path(__file__).parent.absolute().joinpath(respath)
        self.availableComponents = self.loadcomponents(path=respath)
        self.drawnComponents = {}
        self.__nextComponentID = -1
        self.wires = []
        self.wireCount = 0
        self.curComp = self.availableComponents[0]
        self.ghostComp = None

        self.mode = Modes.NORMAL
        self.modefns = defaultdict(NOP_factory)
        # =======+=======+============+============+============+============+============+============+============+============+
        # =======+=======+============+============+============+============+============+============+============+============+
        #  MODE  |>MODIF |> B1        |> B1-R      |> B3        |> B3-R      |> SCROLL    |> MOTION    |> i         | ESC, CTRL+[
        # =======+=======+============+============+============+============+============+============+============+============+
        # NORMAL |       | panStart   | panStop    |            | editComp   |            |            |*insertmode | XXXXXXXXXX
        # INSERT |       |0placeComp  | askCompVals|            | selectComp | cycleComp  | compGhost  |            |*normalmode
        # SELECT |       | boxSelSt   |            |            |            |            |            |*insertmode |*normalmode
        # =======+=======+============+============+============+============+============+============+============+============+
        # NORMAL | SHIFT |            |            |            |            |            |            |            | XXXXXXXXXX
        # INSERT | SHIFT |*lineNode   |            |*lineEnd    |            |            |*drawLine   |            | XXXXXXXXXX
        # SELECT | SHIFT |            |            |            |            |            |            |            | XXXXXXXXXX
        # =======+=======+============+============+============+============+============+============+============+============+
        # NORMAL | CTRL  |            |            |            |            |            |            |            | XXXXXXXXXX
        # INSERT | CTRL  |            |            |            |            |            |            |            | XXXXXXXXXX
        # SELECT | CTRL  |            |            |            |            |            |            |            | XXXXXXXXXX
        # =======+=======+============+============+============+============+============+============+============+============+
        # =======+=======+============+============+============+============+============+============+============+============+
        self.modefns["<Button-1>"].update({
            Modes.NORMAL : self.pan,
            Modes.INSERT : self.placeComponent,
            Modes.SELECT : self.boxSelectStart
        })
        self.modefns["<Shift-Button-1>"].update({
            Modes.INSERT : self.lineNode
        })
        self.modefns["<Shift-Button-3>"].update({
            Modes.INSERT : self.lineEnd
        })
        self.modefns["<Motion>"].update({
            Modes.INSERT : self.componentGhost
        })
        self.modefns["<Shift-Motion>"].update({
            Modes.INSERT : self.drawLine
        })
        self.modefns["i"].update({
            Modes.NORMAL : self.insertmode,
            Modes.SELECT : self.insertmode
        })
        self.modefns["<Escape>"].update({
            Modes.INSERT : self.normalmode,
            Modes.SELECT : self.normalmode
        })
        self.modefns["<Control-bracketleft>"].update({
            Modes.INSERT : self.normalmode,
            Modes.SELECT : self.normalmode
        })
        print(f"Default [i][INSERT]: {self.modefns['i'][Modes.INSERT]}")

        for e in self.modefns:
            bindmodefn(self, e)
        self.bind('<Enter>', lambda e: self.focus_set()) # Catch keyboard events

        self.configure(background='#FFFAF0')

        self.statusbar = Statusbar(self)
        self.statusbar.grid(row=1,column=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    # ============ END OF INIT ========================================================================================

    def create_circle(self, x, y, r, **kwargs):
        """
        Creates a circle at (x,y) with radius r
        kwargs are passed on to tkinter.Canvas.create_oval
        """
        return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)

    def evalModeFn(self, evtstr):
        """
        Shenaniganery to do with dispatching an event to the correct handler based on the current mode
        """
        return lambda e: self.modefns[evtstr][self.mode](e)

    # ============ MODE SWITCHING =====================================================================================
    def normalmode(self, e):
        self.configure(cursor='arrow')
        self.mode = Modes.NORMAL
        self.statusbar.setMode(self.mode)

    def selectmode(self, e):
        self.mode = Modes.SELECT
        self.statusbar.setMode(self.mode)

    def insertmode(self, e):
        self.configure(cursor='cross')
        self.mode = Modes.INSERT
        self.statusbar.setMode(self.mode)

        self.last['ghost'] = self.last['lineStart']
    # ============ END MODE SWITCHING =================================================================================

    def boxSelectStart(self, e):
        print(f"BOX SELECT START {(e.x,e.y)}")

    def pan(self, e):
        print(f"PAN START {(e.x,e.y)}")

    @property
    def nextNode(self):
        self.__nextNode += 1
        return self.__nextNode

    @property
    def nextComponentID(self):
        self.__nextComponentID += 1
        return self.__nextComponentID

    def tagAt(self, tag, p, ignoreIDs = []):
        ov = self.find_overlapping(
                p.x - self.hitradius, p.y - self.hitradius,
                p.x + self.hitradius, p.y + self.hitradius)
        return [e for e in ov if tag in self.gettags(e) and e not in ignoreIDs] # All line segments overlapping

    def wiresAt(self, p, ignoreID = None):
        lsegs = self.tagAt(Wire.__tag__, p, [ignoreID])
        # TODO return actual wire object
        return lsegs

    def controlPointAt(self, p):
        ccids = self.tagAt(Controlpoint.__tag__, p)
        if not ccids:
            return None
        cpid = ccids[0]
        cptags = self.gettags(cpid)
        compLabel = cptags[1]
        compCpLabel = cptags[2]
        if compLabel in self.drawnComponents:
            comp = self.drawnComponents[compLabel]
            print(F"COMPONENT {compLabel} found for CP {cptags[2]}")
            if compCpLabel in comp.controlpoints:
                cp = comp.controlpoints[compCpLabel]
                print(F"CONTROLPOINT OBJ {c} found for CONTROLPOINT {compLabel}")
                return cp
            else:
                raise Exception(F"CONTROLPOINT {compCpLabel} not found among COMPONENT {compLabel}'s controlpoints")
        else:
            raise Exception(F"COMPONENT {compLabel} not found in {self.drawnComponents}")
        # TODO return new controlpoint?
        return None

    def lineNode(self, event):
        pe = self.getSnapPoint(Point(event.x, event.y),self.gridSize)
        if self.lineDraw:
            # Set last node coordinates
            if self.lineDir.w or self.lineDir.e:
                self.last['lineStart'] = Point(pe.x , self.last['lineStart'].y)
            else:
                self.last['lineStart'] = Point(self.last['lineStart'].x , pe.y)

            # Check if wires at coords
            ww = self.wiresAt(self.last['lineStart'],ignoreID=self.last['lineID'])
            w = ww[0] if len(ww) > 0 else None
            if w:
                print(F"JOIN WITH {w}")
                w.addGNode(self.last['lineStart'])
            else:
                w = Wire(self)
                print(F"ADDED WIRE {w} TO NET")

            # Now do control point logic
            c = self.controlPointAt(self.last['lineStart'])
            if c:
                print(F"ADD CONTROLPOINT {c} TO WIRE {w}")
                w.addControlpoint(c)
                if w.node:
                    c.node = w.node
                    print(F"ASSIGNED NODE {w.node} to CONTROLPOINT {c}")
                else:
                    if c.node:
                        w.node = c.node
                        print(F"ASSIGNED NODE {c.node} to WIRE {w}")
                    else:
                        n = self.nextNode()
                        print(F"CREATED NEW NODE {n}")
                        w.node = n
                        print(F"ASSIGNED NODE {n} to WIRE {w}")
                        c.node = n
                        print(F"ASSIGNED NODE {n} to CONTROLPOINT {c}")
        else:
            self.last['lineStart'] = self.getSnapPoint(Point(event.x, event.y),self.gridSize)
            self.lineDraw = True
        self.lineDir = getNullDirection()
        self.itemconfigure(f'currentline{self.lineIdx}',width=2)
        self.lineIdx += 1
        print(f"New Node at {pe}, {self.lineDir}")

    def lineEnd(self,event):
        self.lineDraw = False
        self.lineDir = getNullDirection()
        self.delete(f'currentline{self.lineIdx}')
 
    def gridInterval(self, pos, size):
        return (int(pos/size)*size,int(pos/size)*size+size)

    def getSnapPoint(self, point, size):
        dx = self.gridInterval(point.x, size.w)
        dy = self.gridInterval(point.y, size.h)
        return Point(
                dx[1] if abs(dx[0]-point.x) > abs(dx[1]-point.x) else dx[0],
                dy[1] if abs(dy[0]-point.y) > abs(dy[1]-point.y) else dy[0]
                )

    def drawLine(self,event):
        if self.lineDraw:
            self.delete(f'currentline{self.lineIdx}')
            l = self.getSnapPoint(self.last['lineStart'], self.gridSize)
            x,y = l
            pe = self.getSnapPoint(Point(event.x,event.y),self.gridSize)
            # Don't draw until over minimum threshold
            if abs(l.x-pe.x) < self.minDrawThreshold.x and abs(l.y-pe.y) < self.minDrawThreshold.y:
                #print(f"Under minimum threshold {self.last['lineStart']}-{pe} < {self.minDrawThreshold}")
                return
            # Set line drawing direction
            self.lineDir.n = False
            self.lineDir.s = False
            self.lineDir.e = False
            self.lineDir.w = False
            if abs(l.x-pe.x) > abs(l.y-pe.y):
                if l.x<pe.x:
                    self.lineDir.e = True
                else:
                    self.lineDir.w = True
                x,y = pe.x , l.y
            else:
                if l.y<pe.y:
                    self.lineDir.n = True
                else:
                    self.lineDir.s = True
                x,y = l.x  , pe.y

            self.last['lineID'] = self.create_line((l.x, l.y, x, y),fill='red', width=5, tags=(f'currentline{self.lineIdx}', 'wire'))
        self.statusbar.setPosition(Point(event.x,event.y))

    # ============ CONCERNING COMPONENTS AND THEIR CREATION ===========================================================
    def loadcomponents(self,path=''):
        p = Path(path)
        comps = []
        for f in p.glob('*.svg'):
            print(f"Found component svg {f}")
            comps.append(Component(self, f.stem, path).newComponentConstructor())
            #img = Image.open(str(f)).convert("RGBA")
            print(f"Found component img {f}: img {comps[-1].img} {comps[-1].img.size}")
            #comps.append(ImageTk.PhotoImage(img))
        print(F"Loaded {len(comps)} components")
        return comps

    # COMPONENT DRAWING ===============================================================================================
    def componentGhost(self, e):
        if self.ghostComp is None:
            w,h = self.curComp.photoimg.width(),self.curComp.photoimg.height()
            self.ghostComp = self.create_rectangle(e.x-w/2,e.y-h/2,e.x+w/2,e.y+h/2,tags=('ghost'))
            self.last['ghost'] = Point(e.x, e.y)#self.getSnapPoint(Point(e.x,e.y),self.gridSize)
            #print(F"GHOSTCOMP CREATED: {repr(self.ghostComp)} FROM None")
        else:
            d = Point(e.x - self.last['ghost'].x, e.y - self.last['ghost'].y)
            self.move(self.ghostComp, d.x, d.y)
            self.tag_raise('ghost')
        self.last['ghost'] = Point(e.x, e.y)#self.getSnapPoint(Point(e.x,e.y),self.gridSize)

    def placeComponent(self, e):
        pe = self.getSnapPoint(Point(e.x,e.y),self.gridSize)
        # FIXME this should add new Component objects
        c = self.curComp(self.nextComponentID)
        c.draw(pe)
        self.drawnComponents.update({str(c.comp_id) : c})

    def rotateComponent(self, e):
        # TODO change this to use current selection
        #self.drawnComponents.rotate(1)
        pass

    # END COMPONENT DRAWING ===========================================================================================
    # ============ END OF CONCERNING COMPONENTS =======================================================================

if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    canvas = CircuitCanvas(root,'res')
    canvas.bind('<Control-q>', lambda e: root.quit())
    root.mainloop()
