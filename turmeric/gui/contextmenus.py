from tkinter import *
from tkinter import ttk

class ContextMenu(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.master = master
        self.grid()
        self.widgets()

    def widgets(self):
        components = ['Diode','Resistor','Capacitor']
        menu = Menu(self.master)
        
        for c in components:
            menu.add_command(label = c, command = lambda : print(f"ADD COMPONENT {c}"))

        if (self.master.tk.call('tk', 'windowingsystem') == 'aqua'):
            self.master.bind('<2>', lambda e: menu.post(e.x_root, e.y_root))
            self.master.bind('<Control-1>', lambda e: menu.post(e.x_root, e.y_root))
        else:
            self.master.bind('<3>', lambda e: menu.post(e.x_root, e.y_root))

