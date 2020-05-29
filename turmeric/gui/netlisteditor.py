from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class NetlistEditor(ScrolledText):
    def __init__(self, master, filepath=None):
        super().__init__(master)
        self.master = master
        self.grid(row=0, column=0, sticky=(N,S,E,W))

        self.filepath = filepath

        if self.filepath is not None:
            with open(filepath, 'r') as f:
                self.insert(INSERT,f.read())

        self.bind('<KeyRelease>', self.onKRelease)

    def onKRelease(self,e):
        pass

if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    with open('netlists/OP/diodemulti.net') as f:
        ne = NetlistEditor(root,f.read())
    ne.bind('<Control-q>', lambda e: root.quit())
    root.mainloop()
