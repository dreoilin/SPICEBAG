from tkinter import *
from tkinter import ttk
from tkinter import font

from collections import namedtuple

class Statusbar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style="statusbar.TFrame")

        self.grid(row=1,column=0,columnspan=100,sticky="swe")
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)

        self.master = master

        self.posV = StringVar()
        self.posL = ttk.Label(self,textvariable=self.posV,style='statusbar.TLabel',width=11)
        self.posV.set('(XXXX,YYYY)')
        self.posL.grid(row=0,column=19,sticky=E)

        # Set defaults
        self.setPosition((0,0))

    def setPosition(self, rc):
        self.posV.set(f" {rc[0]:n>},{rc[1]:n<} ")
