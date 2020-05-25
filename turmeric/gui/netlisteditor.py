from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .statusbar import Statusbar

class NetlistEditor(ScrolledText):
    def __init__(self, master, filedata=None):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        if filedata is not None:
            self.insert(INSERT,filedata)
