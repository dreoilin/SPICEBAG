from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .statusbar import Statusbar

class PlainTextEditor(ScrolledText):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky=(N,S,E,W))
