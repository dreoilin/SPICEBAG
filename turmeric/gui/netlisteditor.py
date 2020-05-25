from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .statusbar import Statusbar

class NetlistEditor(ScrolledText):
    def __init__(self, master, filedata=None):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        self.statusbar = Statusbar(self)
        self.statusbar.grid(row=1,column=0,sticky=(S,W,E))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        if filedata is not None:
            self.insert(INSERT,filedata)

        self.bind('<ButtonRelease-1>', self.onBRelease1)
        self.bind('<KeyRelease>', self.onKRelease)

    def onBRelease1(self,e):
        self.updateStatusbar(e)

    def onKRelease(self,e):
        self.updateStatusbar(e)

    def updateStatusbar(self,e):
        rcs = self.index(INSERT)
        rc = rcs.split('.')
        self.statusbar.setPosition((rc[0],rc[1]))
