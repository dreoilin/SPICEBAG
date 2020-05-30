from tkinter import *
from tkinter.dialog import Dialog
import tkinter.ttk as ttk
import json
import re
from abc import ABC, abstractmethod

class ValidatingEntry(Entry, ABC):
    def __init__(self, master, value="", **kwargs):
        super(ValidatingEntry, self).__init__(master, **kwargs)
        self.__value = value
        self.__variable = StringVar()
        self.var = self.__variable
        self.__variable.set(value)
        self.__variable.trace("w", self.__callback)
        self.config(textvariable=self.__variable)

    def __callback(self, *dummy):
        value = self.__variable.get()
        newval = self.validate(value)
        if newval is None:
            self.__variable.set(self.__value)
        elif newval != value:
            self.__value = newval
            self.__varibale.set(self.newval)
        else:
            self.__value = value

    @abstractmethod
    def validate(self, value):
        pass

class FloatEntry(ValidatingEntry):
    def validate(self, value):
        try:
            if value:
                v = float(value)
                return value
        except ValueError:
            return None

class IntEntry(ValidatingEntry):
    def validate(self, value):
        try:
            if value:
                v = int(value)
                return value
        except ValueError:
            return None

class ScrollFrame(ttk.Frame):
    def __init__(self, master, config):
        super().__init__(master)
        self.master = master
        self.canvas = Canvas(master, borderwidth=0)
        self.frame = Frame(self.canvas)
        self.scrollbar = Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.canvas.create_window((1,1), window=self.frame, anchor="nw",tags="self.frame")
        self.frame.bind("<Configure>", self.onFrameConfigure)

        self.config = config
        self.valueWidgets = {
                'bool'  : self.boolWidget,
                'float' : self.floatWidget,
                'str'   : self.strWidget,
                'int'   : self.intWidget,
                'enum'  : self.enumWidget
                }
        self.typefns = {
                'bool'  : bool,
                'float' : float,
                'str'   : str,
                'int'   : int,
                'enum'  : str
                }

        self.valueFieldWidth = 5
        self.nameWrapLength = 150
        self.descWrapLength = 250

        self.populate()

    def populate(self):
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.config_widgets = {}
        for i, kv in enumerate(self.config.items()):
            k, desc = kv
            Label(self.frame, text=k).grid(sticky=W, row=i, column=0)
            self.config_widgets[k] = self.valueWidgets[desc['type']](self.frame, desc)
            self.config_widgets[k].grid(sticky=W, row=i, column=1)
            Label(self.frame, text=str(desc['description']),wraplength=self.descWrapLength).grid(sticky=W, row=i, column=2)

    def dump_config(self):
        ret = {}
        for k,v in self.config_widgets.items():
            value = v.var.get()
            typefn = self.typefns[self.config[k]['type']]
            ret[k] = self.config[k]
            try:
                ret[k]['value'] = typefn(value)
            except ValueError as e:
                logging.exception(f'Invalid value {value} for settings variable {k}. Using previous value.')
                ret[k]['value'] = self.config[k]['value']
        return ret

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def boolWidget(self, master, desc):
        value = desc['value']
        var = IntVar()
        var.set(0)
        if bool(value):
            var.set(1)
        else:
            var.set(0)
        w = ttk.Checkbutton(master, variable=var)
        w.var = var
        return w

    def floatWidget(self, master, desc):
        value = desc['value']
        w = FloatEntry(master, value, width=self.valueFieldWidth)
        return w

    def strWidget(self, master, desc):
        value = desc['value']
        var = StringVar()
        var.set(value)
        w = Entry(master, bg="white", textvariable=var, width=self.valueFieldWidth)
        w.var = var
        return w
    
    def intWidget(self, master, desc):
        value = desc['value']
        w = IntEntry(master, value, width=self.valueFieldWidth)
        return w

    def enumWidget(self, master, desc):
        try:
            enum = set(desc['enum'])
        except KeyError as e:
            logging.exception(f'Enum setting does not have a specified enum')
        var = StringVar()
        var.set(desc['value'])
        w = OptionMenu(master, var, *enum)
        w.configure(width=self.valueFieldWidth)
        w.var = var
        return w


class ConfigWindow(object):
    # Code adapted from tkinter's FileDialog window
    # At https://github.com/python/cpython/blob/3.9/Lib/tkinter/filedialog.py
    def __init__(self, master, config_filename, geometry, title=None):
        self.top = Toplevel(master,padx=5,pady=5)
        self.master = master
        self.top.resizable(True,True)
        self.config_filename = config_filename

        self.top.title( title if title is not None else f'Editing configuration at {self.config_filename}')
        (width, height, x, y) = geometry
        self.top.geometry("%dx%d%+d%+d" % (width, height, x, y))

        self.top.attributes('-type','dialog')

        self.botframe = Frame(self.top)
        self.botframe.pack(side=BOTTOM, fill=X)

        #self.varsBar = Scrollbar(self.varsframe)
        #self.varsBar.pack(side=RIGHT, fill=Y)
        #self.vars = Listbox(self.varsframe, exportselection = 0, yscrollcommand=(self.varsBar, 'set'))
        #self.vars.pack(side=RIGHT, expand=YES, fill=BOTH)
        #self.varsBar.config(command=(self.vars, 'yview'))
        # Could use bindtags to populate varname, value, description fields
        with open(self.config_filename, 'r') as f:
            self.config = json.load(f)
        self.varsframe = ScrollFrame(self.top, self.config)
        self.varsframe.pack(side=TOP, fill=BOTH, expand=True)

        self.ok_button = Button(self.botframe, text="OK", command=self.ok_command)
        self.ok_button.pack(side=LEFT)
        #self.filter_button = Button(self.botframe, text="FILTER", command=self.filter_command)
        #self.filter_button.pack(side=LEFT, expand=YES)
        self.cancel_button = Button(self.botframe, text="Cancel", command=self.cancel_command)
        self.cancel_button.pack(side=RIGHT)

        self.top.protocol('WM_DELETE_WINDOW', self.cancel_command)


    def go(self):
        self.new_config = None
        self.master.mainloop()
        self.top.destroy()
        return self.new_config

    def quit(self, new_config=None):
        self.new_config = new_config
        self.master.quit()

    def ok_command(self):
        self.quit(self.varsframe.dump_config()) # Return new config

    def cancel_command(self):
        self.quit() # Return None, to signify no change

def configdialog(root, filename, geometry=(530,300,0,0), title=None):
    cw = ConfigWindow(root, filename, geometry, title)
    return cw.go()

if __name__ == '__main__':
    root = Tk()
#    cw = ConfigWindow(root,'config.json',(200,300,0,0))
#    new_config = cw.go()
    print(configdialog(root,'config.json'))
