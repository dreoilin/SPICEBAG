import os
import pathlib
import queue
import subprocess
from threading import Thread
from tkinter import *
from tkinter import ttk


class EmbeddedConsole(Text):
    def __init__(self,master,envfilename='turmeric/gui/interactive_console.py'):
        super().__init__(master, wrap=WORD)
        self.master = master

        self.pack(fill=BOTH,expand=True)
        self.bind('<Return>', self.onReturn)

        self.READONLY = 'readonly'
        self.tag_config(self.READONLY)

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
        Thread(target=self.readStdout).start()
        Thread(target=self.readStderr).start()

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

    def __sendLine(self):
        line = self.get(self.LINE_START, END)
        self.python.stdin.write(line.encode())
        self.python.stdin.flush()

    def write(self, text, readonly=True):
        """
        Write data to Text field
        """
        if readonly:
            self.tag_add(self.READONLY, self.LINE_START, f"{self.LINE_START} lineend")
            text = text + '\n'

        self.START_MARK = 'start_mark' # Where text started being added
        self.mark_set(self.START_MARK, INSERT)
        self.mark_gravity(self.START_MARK, LEFT)

        self.insert(END, text)

        self.see(INSERT)

        if readonly:
            self.tag_add(self.READONLY, self.START_MARK, f"{INSERT}-1c")
            self.mark_set(self.LINE_START, INSERT)

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

class EmbeddedConsoleFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.tty = EmbeddedConsole(self)
        # TODO: use grid layout
        self.tty.pack(fill=BOTH,expand=True)

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
