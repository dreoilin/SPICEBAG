from pathlib import Path
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox

from .tabcontrols import TabEditor
from .EditorFrame import EditorFrame
from .configdialog import configdialog

import turmeric.settings
from turmeric.config import load_config, write_config

UNTITLED = 'Untitled'

class Editor(Tk):
    def __init__(self):
        super().__init__()
        self.option_add('*tearOff', FALSE)
        #self.attributes('-type','dialog')
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

        self.read_config()

        self.make_menu()

        self.pwd = Path('.').resolve()
        self.editors = []
        self.tabeditor=TabEditor(self)

    def read_config(self):
        font.nametofont("TkDefaultFont").configure(family="Cantarell")
        font.nametofont("TkTextFont").configure(family="Cantarell")
        font.nametofont("TkMenuFont").configure(family="Cantarell")
        font.nametofont("TkHeadingFont").configure(family="Cantarell")
        font.nametofont("TkCaptionFont").configure(family="Cantarell")
        font.nametofont("TkSmallCaptionFont").configure(family="Cantarell")
        font.nametofont("TkIconFont").configure(family="Cantarell")
        font.nametofont("TkTooltipFont").configure(family="Cantarell")

        s = ttk.Style()
        s.theme_create( "TurmericStyle", parent="alt", settings={
            "TNotebook"        : {"configure" : {"tabmargins": [1, 0, 1, 0] }},
            "TNotebook.Tab"    : {"configure" : {"padding": [3, 1, 3, 1] }},
            "statusbar.TFrame" : {"configure" : {"background": "white"}},
            "statusbar.TLabel" : {"configure" : {
                "background" : "white", "font" : font.nametofont("TkFixedFont")}}
            })
        s.theme_use("TurmericStyle")

    def make_menu(self):
        self.menubar = Menu(self)
        menu_file = Menu(self.menubar)
        menu_edit = Menu(self.menubar)
        self.menubar.add_cascade(menu=menu_file, label='File', underline = 0)
        self.menubar.add_cascade(menu=menu_edit, label='Edit', underline = 0)
        self.menubar.add_command(label='Run', underline = 0, command=self.run)
        self.bind('<Control-r>', self.run)
        menu_file.add_command(label='New', underline = 0, accelerator='Ctl N', command = self.new_editor_tab)
        self.bind('<Control-n>', self.new_editor_tab)
        menu_file.add_command(label='Open...', underline = 0, command=self.open_file)
        self.bind('<Control-o>', lambda e: self.open_file(e))

        menu_file_openrecent = Menu(menu_file)
        menu_file.add_cascade(menu = menu_file_openrecent, label='Open Recent', underline = 5) # TODO
        recentfiles = ['filethefirsct.ckt', 'netlistyboi.net', 'nuddercirquite.ckt']
        for f in recentfiles:
            # This don't quite work but hey
            menu_file_openrecent.add_command(label = f, command = lambda : print(f'OPEN {self}')) # TODO
        
        menu_file.add_command(label='Save', underline = 0, command = self.save_file, state='disabled') # Set `state` to 'normal' to enable
        self.bind('<Control-s>', self.save_file) # TODO Respect disabled flag
        menu_file.add_command(label='Save As', underline = 5, command = lambda : print('Save As'), state='disabled') # TODO
        # There is a tkinter asksaveasfilename() dialog
        menu_file.add_separator()
        menu_file.add_command(label='Quit', accelerator='Ctl+Q', underline = 0, command = self.close) # TODO Wrap this in something to check no unsaved changes
        self.bind('<Control-q>', lambda e: self.close())
        menu_edit.add_command(label='Undo', accelerator='Ctl+Z', command= lambda : print('UNDO')) # TODO
        self.bind('<Control-z>', lambda e: print('UNDO'))
        menu_edit.add_command(label='Redo', accelerator='Ctl+^Z', command= lambda : print('REDO')) # TODO
        self.bind('<Control-Z>', lambda e: print('REDO'))
        menu_edit.add_command(label='Configuration', command= self.open_configuration)

        menu_edit.entryconfigure('Undo', state=DISABLED)
        menu_edit.entryconfigure('Redo', state=DISABLED)
        
        menu_help = Menu(self.menubar, name='help')
        self.menubar.add_cascade(menu=menu_help, label='Help', underline=0)
        menu_help.add_command(label = 'Online Help', underline = 7, command = lambda : print('OPEN URL OF ONLINE HELP'))

        # Windows system menu
        sysmenu = Menu(self.menubar, name='system')
        sysmenu.add_command(label='Enter Narnia', underline = 5, command = lambda : print('COMMAND _enterNarnia NOT YET IMPLEMENTED'))
        self.menubar.add_cascade(menu=sysmenu)

        self.config(menu=self.menubar)

    def close(self, e=None):
        
        self.quit()

    def run(self, e=None):
        frame = self.tabeditor.currentFrame()
        if isinstance(frame, EditorFrame):
            frame.run_netlist()

    def new_editor_tab(self,e=None,filename=None):
        filepath = Path(filename).relative_to(self.pwd) if filename is not None else UNTITLED
        frame = EditorFrame(self.tabeditor,filepath)
        self.editors.append(frame)
        t = self.tabeditor.addtab(filepath,frame=frame)
        frame.netlisteditor.focus_set()
        self.tabeditor.select(t)

    def open_file(self, e=None):
        files = filedialog.askopenfilenames(parent=self.master,title='Open Netlist',filetypes=[('Netlist','*.net')])
        for f in files:
            if '.net' in Path(f).suffixes:
                self.new_editor_tab(filename=f)
            else:
                print("IMPLEMENT EDITOR FOR OTHER FILES") # TODO

    def save_file(self, event=None, filename=None):
        savefilename = self.tabeditor.tab(self.tabeditor.select(), option='text') if filename is None else filename
        if savefilename == UNTITLED:
            self.save_file_as(event)
        else:
            f = open(savefilename, 'w')
            f.write(self.tabeditor.currentFrame().netlisteditor.get(1.0,END))
            f.close()
    
    def save_file_as(self, event=None, text=None):
        f = filedialog.asksaveasfilename(filetypes=[('Netlist','*.net'),('Any','*')])
        if f is not None:
            self.save_file(event,filename=f)
            self.tabeditor.tab(self.tabeditor.select(), text=str(Path(f).relative_to(self.pwd)))

    def open_configuration(self, event=None):
        new_config = configdialog(self, turmeric.settings.config_filename)
        if new_config is not None:
            load_config(configdict=new_config)
            write_config(configdict=new_config,configfile=str(new_config['config_filename']['value']))

if __name__ == '__main__':
    ed = Editor()
    ed.mainloop()
