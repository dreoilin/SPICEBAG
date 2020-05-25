from tkinter import *
from tkinter import ttk
from tkinter import font

from collections import namedtuple

from .mode import Modes, MODESTRS, MODEFMT

Point = namedtuple('Point', 'x y')

class Statusbar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="statusbar.TFrame")

        self.grid(row=1,column=0,columnspan=100,sticky="swe")
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)

        self.master = master

        self.modeV = StringVar()
        self.modeL = ttk.Label(self,textvariable=self.modeV,style='statusbar.TLabel',width=11)
        self.modeV.set('Status text')
        self.modeL.grid(row=0,column=20,sticky=E)

        self.posV = StringVar()
        self.posL = ttk.Label(self,textvariable=self.posV,style='statusbar.TLabel',width=11)
        self.posV.set('(XXXX,YYYY)')
        self.posL.grid(row=0,column=19,sticky=E)

        # Set defaults
        self.setMode(Modes.NORMAL) 
        self.setPosition(Point(0,0))

    def setMode(self, newmode):
        self.modeV.set(MODEFMT.format(MODESTRS[newmode]))

    def setPosition(self, p):
        self.posV.set(f" {p.x:n>},{p.y:n<} ")
