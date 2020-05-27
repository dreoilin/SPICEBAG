import os
import pathlib
import queue
import subprocess
from threading import Thread
from tkinter import *
from tkinter import ttk


class ConsoleFrame(ttk.Frame):
    def __init__(self,master,envfilename='turmeric/gui/interactive_console.py'):
        super().__init__(master)
        self.master = master
        self.createUI()

        consoleFile = pathlib.Path('.').resolve() / envfilename
        self.python = subprocess.Popen(["python3",str(consoleFile)],
                stdin =subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        self.outBuf = queue.Queue()
        self.errBuf = queue.Queue()

        self.line_idx = 0

        # Insert cursor position on entry line
        self.SCROLL_MARK = 'scroll_mark'
        self.mark_set(self.SCROLL_MARK, END)
        self.mark_gravity(self.mark, RIGHT)
        # Start of user input (just after prompt)
        self.LINE_START = 'line_start'
        self.mark_set(self.line_start, INSERT)
        self.mark_gravity(self.line_start, LEFT)

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
        
        for w in self.widgets:
            w.destroy()
        super().destroy()

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
            self.write(self.errBuf.get())
        if not self.outBuf.empty():
            self.write(self.outBuf.get())

        if self.alive:
            self.after(10, self.pollOutputStreams)

    def write(self, text, editable=False):

        self.tty.insert(END, text)
        self.tty.see(END)
        self.line_idx += len(text)

    def createUI(self):
        self.widgets = []
        self.tty = Text(self, wrap=WORD)
        # TODO: use grid layout
        self.tty.pack(fill=BOTH,expand=True)
        self.tty.bind('<Return>', self.onReturn)
        self.widgets.append(self.tty)

    def onReturn(self, e):
        line = self.tty.get(1.0, END)[self.line_idx:]
        self.line_idx += len(line)
        self.python.stdin.write(line.encode())
        self.python.stdin.flush()
