from tkinter import *
from tkinter.dialog import Dialog
import tkinter.ttk as ttk
import json

class VarDetails(ttk.Frame):
    def __init__(self, master, name, desc):
        super().__init__(master)
        self.master = master

        self.nameVar = StringVar()
        self.nameVar.set(name)
        self.nameL = Label(self, textvariable=self.nameVar)
        self.nameL.pack(side=LEFT,fill=X)

        self.descriptionVar = StringVar()
        self.descriptionVar.set(desc['description'])
        self.descriptionL = Label(self, textvariable=self.descriptionVar)
        self.descriptionL.pack(side=LEFT, fill=X)

        self.pack(expand=YES,fill=X)

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
        # create window?
        self.canvas.create_window((4,4), window=self.frame, anchor="nw",tags="self.frame")
        self.frame.bind("<Configure>", self.onFrameConfigure)

        self.config = config
        self.populate()

    def populate(self):
        for i, kv in enumerate(self.config.items()):
            k, desc = kv
            Label(self.frame, text=k).grid(sticky=W, row=i, column=0)
            Label(self.frame, text=str(desc['value'])).grid(sticky=W, row=i, column=1)
            Label(self.frame, text=str(desc['description'])).grid(sticky=W, row=i, column=2)
            #self.vars.insert(END, VarDetails(self.vars, k, desc))

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))



class ConfigWindow(object):
    # Code adapted from tkinter's FileDialog window
    # At https://github.com/python/cpython/blob/3.9/Lib/tkinter/filedialog.py
    def __init__(self, master, config_filename, geometry, title=None):
        self.top = Toplevel(master)
        self.master = master
        
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
        self.quit(self.config) # Return new config

    def cancel_command(self):
        self.quit() # Return None, to signify no change

def configdialog(root, filename, geometry=(400,600,0,0), title=None):
    cw = ConfigWindow(root, filename, geometry, title)
    return cw.go()

if __name__ == '__main__':
    root = Tk()
#    cw = ConfigWindow(root,'config.json',(200,300,0,0))
#    new_config = cw.go()
    print(configdialog(root,'config.json'))
