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
        self.wm_title("Turmeric Integrated Simulation Environment")

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
        menu_file.add_command(label='New', underline = 0, accelerator='Ctl+N', command = self.new_editor_tab)
        self.bind('<Control-n>', self.new_editor_tab)
        menu_file.add_command(label='Open...', underline = 0, command=self.open_file)
        self.bind('<Control-o>', lambda e: self.open_file(e))

        menu_file.add_command(label='Save', underline = 0, command = self.save_file, accelerator='Ctl+S')
        self.bind('<Control-s>', self.save_file)
        menu_file.add_command(label='Save As...', underline = 5, command = self.save_file_as, accelerator='Ctl+Alt+S')
        self.bind('<Control-Alt-a>', self.save_file_as)
        menu_file.add_separator()
        menu_file.add_command(label='Quit', accelerator='Ctl+Q', underline = 0, command = self.close)
        self.bind('<Control-q>', lambda e: self.close())

        # Some text edit commands inbuilt
        menu_edit.add_command(label='Undo', accelerator='Ctl+Z', command=self.undo) 
        menu_edit.add_command(label='Redo', accelerator='Ctl+^Z', command=self.redo)
        menu_edit.add_separator()
        menu_edit.add_command(label='Copy', accelerator='Ctl+C', command=self.copy)
        #self.bind('<Control-c>', self.copy)
        menu_edit.add_command(label='Cut', accelerator='Ctl+X', command=self.cut)
        #self.bind('<Control-x>', self.cut)
        menu_edit.add_command(label='Paste', accelerator='Ctl+V', command=self.paste)
        #self.bind('<Control-v>', self.paste)
        menu_edit.add_separator()
        menu_edit.add_command(label='Select All', accelerator='Ctl+A', command=self.select_all)
        self.bind('<Control-a>', self.select_all)
        menu_edit.add_separator()
        menu_edit.add_command(label='Configuration', command= self.open_configuration)

        #menu_help = Menu(self.menubar, name='help')
        #self.menubar.add_cascade(menu=menu_help, label='Help', underline=0)
        #menu_help.add_command(label = 'Online Help', underline = 7, command = lambda : print('OPEN URL OF ONLINE HELP'))

        # Windows system menu
        #sysmenu = Menu(self.menubar, name='system')
        #sysmenu.add_command(label='Enter Narnia', underline = 5, command = lambda : print('COMMAND _enterNarnia NOT YET IMPLEMENTED'))
        #self.menubar.add_cascade(menu=sysmenu)

        self.config(menu=self.menubar)

    def close(self, e=None):
        
        self.quit()

    def run(self, e=None):
        frame = self.tabeditor.currentFrame()
        if isinstance(frame, EditorFrame):
            frame.run_netlist()

    def new_editor_tab(self,e=None,filename=None):
        filepath = Path(filename).relative_to(self.pwd) if filename is not None else None
        title = filepath if filepath is not None else UNTITLED
        frame = EditorFrame(self.tabeditor,filepath=filepath)
        self.editors.append(frame)
        t = self.tabeditor.addtab(title,frame=frame)
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

    # Text editing
    def redo(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            ned.edit_redo()

    def undo(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            ned.edit_undo()

    def copy(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            self.clipboard_clear()
            self.clipboard_append(ned.get(SEL_FIRST,SEL_LAST))

    def cut(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            self.clipboard_clear()
            self.clipboard_append(ned.get(SEL_FIRST,SEL_LAST))
            ned.delete(SEL_FIRST, SEL_LAST)

    def paste(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            ned.insert(INSERT, self.clipboard_get())

    def select_all(self, e=None):
        ed = self.tabeditor.currentFrame()
        if ed:
            ned = ed.netlisteditor
            ned.tag_add(SEL, '1.0', END)


if __name__ == '__main__':
    ed = Editor()
    ed.mainloop()
