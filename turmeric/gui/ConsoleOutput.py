from tkinter import *
import tkinter.ttk as ttk
from tkinter.scrolledtext import ScrolledText

from turmeric.gui.tabcontrols import TabEditor

class ConsoleOutput(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

        self.tabe = TabEditor(self)
        self.tabe.grid(row=0, column=0, sticky="nsew")

        self.oTab = self.tabe.addtab(text='stdout',frame=ScrollFrame(self))
        self.eTab = self.tabe.addtab(text='stderr',frame=ScrollFrame(self))

    def writeOutput(self, text):
        self.oTab.writeline(text)

    def writeError(self, text):
        self.tabe.select(self.eTab)
        self.eTab.writeline(text)

class ScrollFrame(Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.grid(row=0,column=0,sticky="nsew")
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        self.txt = ScrolledText(self,state='disabled',background='#ffffff')
        self.txt.grid(row=0,column=0,sticky="nsew")

    def write(self, text):
        self.txt.configure(state='normal')
        self.txt.insert('end', text)
        self.txt.configure(state='disabled')

    def writeline(self, text):
        self.write(text+'\n')
