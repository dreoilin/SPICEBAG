from tkinter import *
from tkinter import ttk
from turmeric.gui.netlisteditor import NetlistEditor
from turmeric.gui.statusbar import Statusbar
from turmeric.gui.EmbeddedConsole import EmbeddedConsoleFrame

class EditorFrame(ttk.Frame):
    def __init__(self, master, filepath=None):
        super().__init__(master)
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        paneH = ttk.PanedWindow(self,orient=HORIZONTAL)
        paneVL = ttk.PanedWindow(paneH,orient=VERTICAL)
        self.netlisteditor = NetlistEditor(paneVL,filepath)
        self.console = EmbeddedConsoleFrame(paneVL)#Label(paneVL,text="CONSOLE")
        self.plot = Label(paneH,text="PLOT OF RESULTS")

        paneH.grid(row=0,column=0,sticky=NSEW)
        paneVL.add(self.netlisteditor, weight=1)
        paneVL.add(self.console,weight=1)
        paneH.add(paneVL, weight=1)
        paneH.add(self.plot,weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.netlisteditor.grid_propagate(0)
        self.console.grid_propagate(0)
        self.plot.grid_propagate(0)
        self.netlisteditor.columnconfigure(0, weight=1)
        self.console.columnconfigure(0, weight=1)
        self.plot.columnconfigure(0, weight=1)
        self.netlisteditor.rowconfigure(0, weight=1)
        self.console.rowconfigure(0, weight=1)
        self.plot.rowconfigure(0, weight=1)

        self.statusbar = Statusbar(self)
        self.statusbar.grid(row=1,column=0)

        self.netlisteditor.bind('<KeyRelease>', self.onKRelease)
        self.netlisteditor.bind('<ButtonRelease>', self.onBRelease)

    def run_netlist(self):
        print(f"File to run: {self.netlisteditor.filepath}")
        runcmd = f'res = turmeric.main("{self.netlisteditor.filepath}")'
        self.console.tty.run_command(runcmd)

    def onBRelease(self,e):
        self.updateStatusbar(e)

    def onKRelease(self,e):
        self.updateStatusbar(e)

    def updateStatusbar(self,e):
        rcs = self.netlisteditor.index(INSERT)
        rc = rcs.split('.')
        self.statusbar.setPosition((rc[0],rc[1]))

if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    ef = EditorFrame(root,'netlists/OP/diodemulti.net')
    ef.bind('<Control-q>', lambda e: root.quit())
    root.mainloop()
