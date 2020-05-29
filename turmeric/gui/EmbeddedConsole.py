import os
import pathlib
import queue
import subprocess
from threading import Thread
from tkinter import *
from tkinter import ttk

ansi_colour_codes =  {
        'foreground':
        {
            '0;30': 'Black',
            '0;31': 'Red',
            '0;32': 'Green',
            '0;33': 'Brown',
            '0;34': 'Blue',
            '0;35': 'Purple',
            '0;36': 'Cyan',
            '0;37': 'LightGray',
            '1;30': 'DarkGray',
            '1;31': 'DarkRed',
            '1;32': 'SeaGreen',
            '1;33': 'Yellow',
            '1;34': 'LightBlue',
            '1;35': 'MediumPurple',
            '1;36': 'LightCyan',
            '1;37': 'White'
        },
        'background':
        {
            '0;40': 'Black',
            '0;41': 'Red',
            '0;42': 'Green',
            '0;43': 'Brown',
            '0;44': 'Blue',
            '0;45': 'Purple',
            '0;46': 'Cyan',
            '0;47': 'LightGray',
            '1;40': 'DarkGray',
            '1;41': 'DarkRed',
            '1;42': 'SeaGreen',
            '1;43': 'Yellow',
            '1;44': 'LightBlue',
            '1;45': 'MediumPurple',
            '1;46': 'LightCyan',
            '1;47': 'White'
        },
}


class EmbeddedConsole(Text):
    def __init__(self,master,envfilename='turmeric/gui/interactive_console.py'):
        super().__init__(master, wrap=WORD)
        self.master = master

        self.pack(fill=BOTH,expand=True)
        self.bind('<Return>', self.onReturn)
        
        # Output text shouldn't be editable
        self.READONLY = 'readonly'
        self.tag_config(self.READONLY)

        for code in ansi_colour_codes['foreground']:
            self.tag_config(code, foreground=ansi_colour_codes['foreground'][code])
        self.ansi_decompose = re.compile('\x01?\x1b\[(.*)m\x02?')
        self.ansi_escape = re.compile(r'''
            \x1B  # ESC
            (?:   # 7-bit C1 Fe (except CSI)
                [@-Z\\-_]
            |     # or [ for CSI, followed by a control sequence
                \[
                    [0-?]*  # Parameter bytes
                    [ -/]*  # Intermediate bytes
                    [@-~]   # Final byte
            )
        ''', re.VERBOSE)
        # Insert cursor position on entry line
        self.SCROLL_MARK = 'scroll_mark'
        self.mark_set(self.SCROLL_MARK, END)
        self.mark_gravity(self.SCROLL_MARK, RIGHT)
        # Start of user input (just after prompt)
        self.LINE_START = 'line_start'
        self.mark_set(self.LINE_START, INSERT)
        self.mark_gravity(self.LINE_START, LEFT)

        self.__bindings()

        consoleFile = pathlib.Path('.').resolve() / envfilename
        self.python = subprocess.Popen(["python3",str(consoleFile)],
                stdin =subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        self.outBuf = queue.Queue()
        self.errBuf = queue.Queue()
        self.alive = True
        self.read_buf_size = 1024
        threads = [Thread(target=self.readStdout), Thread(target=self.readStderr)]
        for t in threads:
            t.daemon = True
            t.start()
        for t in threads:
            t.join(1)

        self.pollOutputStreams()

    # Called when widget destroyed
    def destroy(self):
        self.alive=False
        self.python.stdin.write("exit()\n".encode())
        self.python.stdin.flush()
        super().destroy()

    # ========================
    # == BINDINGS ============
    # ========================
    def __bindings(self):
        self.bind("<Key>",self.onKPress)
        self.bind("<Return>",self.onReturn)
        self.bind("<Tab>",self.onKTab)
        self.bind("<BackSpace>",self.onKBackspace)

    def onKPress(self, e):
        if self.is_readonly:
            self.mark_set(INSERT, self.SCROLL_MARK)
        self.mark_set(self.SCROLL_MARK, f"{INSERT}+1c")

    def onReturn(self, e):
        self.__sendLine()
        return "break"

    def onKBackspace(self, e):
        if self.is_readonly:
            return "break"

    def onKTab(self, e):
        """
        Mask tab key until completion is implemented
        """
        return "break"

    # ========================
    # == END BINDINGS ========
    # ========================

    @property
    def is_readonly(self):
        ro_ranges = self.tag_ranges(self.READONLY)
        first=None
        # TODO: There has to be a better way of doing this
        for idx in ro_ranges:
            if not first:
                first = idx
                continue
            else:
                if self.compare(INSERT, '>=',first) and self.compare(INSERT,'<=',idx):
                    return True
                first = None
        return False

    def __sendLine(self,line=None):
        line = self.get(self.LINE_START, END) if line is None else line
        self.python.stdin.write(line.encode())
        self.python.stdin.flush()

    def write(self, text, readonly=True, output=True):
        """
        Write data to Text field
        """
        if readonly:
            self.tag_add(self.READONLY, self.LINE_START, f"{self.LINE_START} lineend")
            text = '\n' + text if output else text
        
        # Split on colour code regex
        #rex_segs = self.ansi_decompose.split(text)
        raw = self.ansi_escape.sub('',text)
        #import pdb;pdb.set_trace()
        self.START_MARK = 'start_mark' # Where text started being added
        self.mark_set(self.START_MARK, INSERT)
        self.mark_gravity(self.START_MARK, LEFT)

        #self.insert(END, rex_segs.pop(0)) # First group is text output
        self.insert(END, raw) # First group is text output
        
        #if rex_segs: # Any remaining segments have colour codes associated
        #    colour_tags = self.ansi_decompose.findall(text)
        #    for t in colour_tags:
        #        i = rex_segs.index(t)
        #        self.insert(END, rex_segs[i+1], t)
        #        rex_segs.pop(i)

        if readonly:
            self.tag_add(self.READONLY, self.START_MARK, f"{INSERT}-1c")
            self.mark_set(self.LINE_START, INSERT)

        self.see(INSERT)
        self.mark_unset(self.START_MARK)

    #################################
    def readStdout(self):
        while self.alive:
            s = self.python.stdout.raw.read(self.read_buf_size).decode()
            self.outBuf.put(s)

    def readStderr(self):
        while self.alive:
            s = self.python.stderr.raw.read(self.read_buf_size).decode()
            self.errBuf.put(s)

    def pollOutputStreams(self):
        if not self.errBuf.empty():
            self.write(self.errBuf.get(),readonly=True)
        if not self.outBuf.empty():
            self.write(self.outBuf.get(),readonly=True)

        if self.alive:
            self.after(10, self.pollOutputStreams)

    def run_command(self, command):
        command = command + '\n' if command[-1] != '\n' else command
        self.write(command, readonly=True, output=False)
        self.__sendLine(command)

class EmbeddedConsoleFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid(row=0,column=0,sticky=NSEW)
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)

        self.tty = EmbeddedConsole(self)
        self.tty.grid_propagate(0)
        self.tty.columnconfigure(0, weight=1)
        self.tty.rowconfigure(0, weight=1)

    def destroy(self):
        self.tty.destroy()
        super().destroy()


if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    ec = EmbeddedConsoleFrame(root)
    ec.bind('<Control-q>', lambda e: root.quit())
    root.mainloop()
