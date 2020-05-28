from tkinter import *
from tkinter import ttk

from .statusbar import Statusbar

class TabEditor(ttk.Notebook):
    def __init__(self,master):
        super().__init__(master)
        self.master = master
        self.grid(row=0,column=0,sticky="nsew")
        self.tabs = []

        self.bind('<<NotebookTabChanged>>', self.onTabChange)
        self.bind('<Button-1>', self.onTabB1)
        self.bind('<ButtonRelease-1>', self.onTabB1Released)
        self.master.bind('<Control-w>', self.remove_tab)

        self.enable_traversal()

        self.hiddentabs = []

    def remove_tab(self, e=None, tabid="current"):
        self.forget(tabid)

    def addtab(self, text="", frame=None):
        if frame is None:
            frame = ttk.Frame(self)
            frame.grid()
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
        if len(self.tabs) == 0:
            self.tabs.append(self.add(frame, text=text, compound=TOP))
        else:
            self.tabs.append(self.add(frame, text=text))
        return frame

    def currentFrame(self):
        return self.nametowidget(self.select())

    def onTabChange(self, e):
        #print(f"Tab changed, now {self.select()}")
        pass

    def onTabB1(self, e):
        global srcidx
        srcidx = self.master.tk.call(self,'identify', 'tab',e.x,e.y)
        if srcidx != '':
            self.configure(cursor='trek')
        #print(f"Clicked on {repr(srcidx)} at {(e.x,e.y)}")

    def onTabB1Released(self, e):
        global srcidx, dstidx
        dstidx = self.master.tk.call(self,'identify', 'tab', e.x, e.y)
        dstidx = self.index('end')-1 if dstidx == '' and e.x < self.master.winfo_width() and e.x > 0 and e.y > 0 and e.y < 20 else dstidx
        if srcidx != '' and dstidx != '' and dstidx != srcidx:
            #print(f"Moving {repr(srcidx)} to {repr(dstidx)}{(e.x,e.y)}")
            self.insert(dstidx,srcidx)
        self.configure(cursor='arrow')


if __name__ == '__main__':
    root = Tk()
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    te=TabEditor(root)
    for n in ["ONE","TWO","THREE"]:
        te.addtab(n)


    root.mainloop()
