from tkinter import *
from tkinter import ttk
from tkinter import font

from collections import namedtuple

class Statusbar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="statusbar.TFrame")

        self.master = master

        self.posV = StringVar()
        self.posL = ttk.Label(self,textvariable=self.posV,style='statusbar.TLabel',width=11)
        self.posV.set('(XXXX,YYYY)')
        self.posL.pack(side=RIGHT)

        # Set defaults
        self.setPosition((0,0))

    def setPosition(self, rc):
        self.posV.set(f" {rc[0]:n>},{rc[1]:n<} ")
