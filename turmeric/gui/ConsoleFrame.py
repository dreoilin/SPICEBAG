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

        self.line_start = 0
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

    def write(self, s):
        self.tty.insert(END, s)
        self.tty.see(END)
        self.line_start += len(s)

    def createUI(self):
        self.widgets = []
        self.tty = Text(self, wrap=WORD)
        # TODO: use grid layout
        self.tty.pack(fill=BOTH,expand=True)
        self.tty.bind('<Return>', self.onReturn)
        self.widgets.append(self.tty)

    def onReturn(self, e):
        line = self.tty.get(1.0, END)[self.line_start:]
        self.line_start += len(line)
        self.python.stdin.write(line.encode())
        self.python.stdin.flush()
