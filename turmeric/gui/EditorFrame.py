from tkinter import *
from tkinter import ttk
from netlisteditor import NetlistEditor
from statusbar import Statusbar

class EditorFrame(ttk.Frame):
    def __init__(self, master, netFiledata=None):
        super().__init__(master)
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        paneH = ttk.PanedWindow(self,orient=HORIZONTAL)
        paneVL = ttk.PanedWindow(paneH,orient=VERTICAL)
        self.netlistEditor = NetlistEditor(paneVL,netFiledata)
        lc = Label(paneVL,text="CONSOLE")
        lg = Label(paneH,text="PLOT OF RESULTS")

        paneH.grid(row=0,column=0,sticky=NSEW)
        paneVL.add(self.netlistEditor, weight=1)
        paneVL.add(lc,weight=1)
        paneH.add(paneVL, weight=1)
        paneH.add(lg,weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.netlistEditor.grid_propagate(0)
        lc.grid_propagate(0)
        lg.grid_propagate(0)
        self.netlistEditor.columnconfigure(0, weight=1)
        lc.columnconfigure(0, weight=1)
        lg.columnconfigure(0, weight=1)
        self.netlistEditor.rowconfigure(0, weight=1)
        lc.rowconfigure(0, weight=1)
        lg.rowconfigure(0, weight=1)

        self.statusbar = Statusbar(self)
        self.statusbar.grid(row=1,column=0)

        self.netlistEditor.bind('<KeyRelease>', self.onKRelease)
        self.netlistEditor.bind('<ButtonRelease>', self.onBRelease)

    def onBRelease(self,e):
        self.updateStatusbar(e)

    def onKRelease(self,e):
        self.updateStatusbar(e)

    def updateStatusbar(self,e):
        rcs = self.netlistEditor.index(INSERT)
        rc = rcs.split('.')
        self.statusbar.setPosition((rc[0],rc[1]))

if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    with open('netlists/OP/diodemulti.net') as f:
        ef = EditorFrame(root,f.read())
    ef.bind('<Control-q>', lambda e: root.quit())
    root.mainloop()
