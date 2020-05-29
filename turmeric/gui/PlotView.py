from tkinter import *
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

class PlotView(Frame):
    def __init__(self, master):
        super().__init__(master,background='green')
        self.master = master

        #self.varsframe = Frame(self)
        #self.varsframe.pack(side=LEFT,fill=Y,expand=True)
        self.plotContainer = Frame(self)
        self.plotContainer.pack(side=LEFT, fill=BOTH, expand=Y)

        self._fig = Figure(dpi=100)
        self.subplot = self._fig.add_subplot(1,1,1)
        self.canvas = FigureCanvasTkAgg(self._fig, master=self.plotContainer)
        self.canvas.draw()
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plotContainer)
        self.toolbar.update()

    @property
    def figure(self):
        return self._fig

    def on_key_press(self, e):
        print(f'{e.key} pressed')
        key_press_handler(e, self.canvas, self.toolbar)

    def plot(self):
        analysis = self.analysisSelection.get()
        x = self.res[analysis][self.X]
        for y in [self.res[analysis][yi] for yi in self.Y]:
            if analysis == 'AC':
                x = np.absolute(x)
                yabs = np.absolute(y)
                yph  = np.angle(y)
                self.subplot.plot(x,yabs,linestyle='solid')
                self.subplot.plot(x,yph ,linestyle='dashed')
            else:
                self.subplot.plot(x,y)

    def populateVarSelect(self, res):

        analyses = tuple([ k for k in res.keys() if k != 'OP'])
        self.res = res
        
        if not hasattr(self, 'psframe'):
            self.psframe = Frame(self)
            self.psframe.pack(side=TOP, fill=Y, expand=True)
            self.gridbox = Frame(self.psframe)

            self.analysisSelection = StringVar()
            self.analysisSelection.set(analyses[0])
            if len(analyses) < 2:
                self.aOptLabel = Label(self.gridbox, text=self.analysisSelection.get())
                self.aOptLabel.grid(  row=0,column=0,sticky='ew',columnspan=2)
                self.gridbox.rowconfigure(0, weight=1)
            else:
                self.aOptMenu = OptionMenu(self.gridbox, self.analysisSelection, *analyses, command=self.populate_varlist)
                self.aOptLabel = Label(self.gridbox, text='Select analysis:')
                self.aOptLabel.grid(  row=0,column=0,sticky='ew')
                self.aOptMenu.grid(   row=0,column=1,sticky='ew')

            self.helpL = Label(self.gridbox, text="To plot a range of values:\n  \u2022Select the independent variable\n  \u2022Click `Set X range'\n  \u2022Select one or many variables\n  \u2022Click `Set Y ranges'\n  \u2022Choose an axis type\n  \u2022Click `Plot selection'", justify=LEFT)

            self.paramlb = Listbox(self.gridbox, exportselection=0,selectmode='multiple')
            self.paramlbBar = Scrollbar(self.gridbox, orient=VERTICAL)
            self.paramlb.config(yscrollcommand=self.paramlbBar.set)
            self.paramlbBar.config(command=self.paramlb.yview)
            self.populate_varlist(self.analysisSelection.get())
            
            self.setXB = Button(self.gridbox, text='Set X range', command=self.set_x_range)
            self.setYB = Button(self.gridbox, text='Set Y ranges', command=self.set_y_range)

            self.axesEnum = ('LINEAR XY','SEMILOG X','SEMILOG Y','LOG XY')
            self.axesVar = StringVar()
            self.axesVar.set(self.axesEnum[0])
            self.axesMenu = OptionMenu(self.gridbox, self.axesVar, *self.axesEnum)
            self.axesL = Label(self.gridbox, text='Select axes scale:')

            self.plotB = Button(self.gridbox, text='Plot selection', command=self.plot)

            self.gridbox.grid(row=0, column=0, sticky='nsew')
            self.gridbox.rowconfigure(1, weight=1)
            self.gridbox.columnconfigure(0, weight=1,pad=2)
            self.gridbox.columnconfigure(1, weight=1,pad=2)
            self.gridbox.columnconfigure(2, weight=0)
            self.helpL.grid(      row=1,column=0,sticky='ew', columnspan=2)
            self.paramlb.grid(    row=2,column=0,sticky='ew', columnspan=2)
            self.paramlbBar.grid( row=2,column=2,sticky='nsw')
            self.setXB.grid(      row=3,column=0,sticky='ew')
            self.setYB.grid(      row=3,column=1,sticky='ew')
            self.axesL.grid(      row=4,column=0,sticky='ew')
            self.axesMenu.grid(   row=4,column=1,sticky='ew')
            self.plotB.grid(      row=5,column=0,sticky='ew', columnspan=2)
        self.analysisSelection.set(analyses[0])

        if len(analyses) == 1:
            self.populate_varlist(analyses[0])

    def populate_varlist(self, value):
        self.paramlb.delete(0, END)
        for var in self.res[value]:
            self.paramlb.insert(END, var)
    
    def set_x_range(self, e=None):
        sel = self.paramlb.curselection()
        if not len(sel) > 0:
            return
        x = [self.paramlb.get(i) for i in sel]
        if len(x) > 1:
            # Put this in infoLabel
            print("Too many ranges selected for x")
            return
        self.X = x[0]
        for i in sel:
            self.paramlb.selection_clear(i)
        print(self.X)


    def set_y_range(self, e=None):
        sel = self.paramlb.curselection()
        if not len(sel) > 0:
            return
        y = [self.paramlb.get(i) for i in sel]
        self.Y=y
        for i in sel:
            self.paramlb.selection_clear(i)
        print(self.Y)

if __name__=='__main__':
    root = Tk()
    root.wm_title("Matplotlib Tk embedding")
    frame = PlotView(root)
    # For example
    import numpy as np
    t=np.arange(0,3,.01)
    frame.fig.add_subplot(111).plot(t, 2*np.sin(2*np.pi*t))
    root.mainloop()

