from tkinter import *
from tkinter import ttk, font
from turmeric.analyses.Analysis import analyses_vtypes
from turmeric.gui.netlisteditor import NetlistEditor
from turmeric.results import Solution
from turmeric.gui.statusbar import Statusbar
from turmeric.gui.EmbeddedConsole import EmbeddedConsoleFrame
from turmeric.gui.ConsoleOutput import ConsoleOutput
from turmeric.gui.PlotView import PlotView
from pathlib import Path
import subprocess, queue, threading
import turmeric.settings as settings
import os

class EditorFrame(ttk.Frame):
    def __init__(self, master, filepath=None):
        super().__init__(master)
        self.master = master
        self.pack(side=TOP, fill=BOTH, expand=True)

        paneH = ttk.PanedWindow(self,orient=HORIZONTAL)
        paneVL = ttk.PanedWindow(paneH,orient=VERTICAL)
        self.netlisteditor = NetlistEditor(paneVL,filepath)
        self.netlisteditor.configure(font=font.Font(family="Courier", size=10))
        self.netlisteditor.pack(side=TOP,fill=BOTH,expand=True)
        self.console = ConsoleOutput(paneVL)
        self.console.pack(side=TOP,fill=BOTH,expand=True)
        self.plot = PlotView(paneH)

        paneH.pack(side=TOP, fill=BOTH, expand=True)
        paneVL.add(self.netlisteditor, weight=3)
        paneVL.add(self.console, weight=1)
        paneH.add(paneVL, weight=1)
        paneH.add(self.plot,weight=1)

        self.statusbar = Statusbar(self)
        self.statusbar.pack(side=BOTTOM, fill=X)

        self.netlisteditor.bind('<KeyRelease>', self.onKRelease)
        self.netlisteditor.bind('<ButtonRelease>', self.onBRelease)
        self.netlisteditor.focus_set()

        self.doneQueue = queue.Queue()
        self.worker_stopping = []
        self.finishedError = True

    def start_run_worker(self,filepath):
        #python -u -c 'from turmeric import runnet;runnet("netlists/TRAN/FW_RECT.net")'
        cmd=["python","-u","-m",'turmeric',"-o", settings.outprefix, str(filepath)]
        #print(' '.join(cmd))
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.add_worker_gui()
        self.tk.createfilehandler(self.proc.stdout, READABLE, lambda p,m: self.read_output(p,m,self.console.writeOutput))
        self.tk.createfilehandler(self.proc.stderr, READABLE, lambda p,m: self.read_output(p,m,self.console.writeError))

        #def results_notifier():
        #    while self.doneQueue.empty():
        #        if self.worker_stopping:
        #            return
        #        self.doneQueue.get(block=False,timeout=None)
        #        self.console.writeOutput(f'Analysis complete, results are ready to be loaded from file')

        #threading.Thread(target=results_notifier, daemon=True).start()

    def add_worker_gui(self):
        if not hasattr(self,'CancelButton'):
            self._progressV = StringVar()
            self.CancelButton = Button(self.statusbar, text="Stop running analysis",command=self.stop_worker)
            self.ProgressL = Label(self.statusbar, textvariable=self._progressV, font=("Courier",10))
        self.CancelButton.pack(side=LEFT)
        self.ProgressL.pack(side=LEFT,fill=BOTH,expand=Y)

    def hide_worker_gui(self):
        self.CancelButton.pack_forget()
        self.ProgressL.pack_forget()

    def read_output(self, pipe, mask, printfn):
        data = os.read(pipe.fileno(), 1 << 20)
        if not data: 
            # done
            self.tk.deletefilehandler(self.proc.stdout)
            self.tk.deletefilehandler(self.proc.stderr)
            self.load_results()
            self.after(5000, self.stop_worker)
            return
        s = data.strip(b'\n').decode()
        if s.startswith('\r'):
            self._progressV.set(s)
        else:
            printfn(s)

    def stop_worker(self):
        if self.worker_stopping:
            return
        self.worker_stopping.append(True)

        self.proc.terminate()
        self.hide_worker_gui()
        
    def run_netlist(self):
        self.start_run_worker(self.netlisteditor.filepath)

    def load_results(self, fileprefix=settings.outprefix):
        opfiles = Path(settings.output_directory) / fileprefix
        sol_files = [Path(str(opfiles)+'.'+a) for a in analyses_vtypes.keys() if Path(str(opfiles)+'.'+a).exists()]
        if not sol_files:
            self.console.writeError(f"Failed to parse result data from files with prefix `{opfiles.resolve()}'")
            return
        self.console.writeOutput(f"Results being loaded from `{sol_files}'")
        sols = [Solution(filename=f.name,sol_type=f.suffix[1:]) for f in sol_files]
        
        results = dict(sol.as_dict(v_type=analyses_vtypes[a]) for a, sol in zip([f.suffix[1:] for f in sol_files],sols))

        if 'OP' in results:
            self.printOP(results['OP'])
        results.pop('OP', None)

        self.plot.populateVarSelect(results)
        # self.plot.defaultPlot()
        #self.plot.plot_data(noop[[k for k in noop][0]] if len(noop)>0 else None)
    
    def printOP(self, vals):
        r = 'OP:\n|{:=<12}|{:=<12}|\n|{:^12}|{:^12}|\n|{:=<12}|{:=<12}|\n'.format('','','Quantity','Value','','')
        for k,v in vals.items():
            r+= f'| {k:<11}|{v[0]:> 12.6g}|\n'
        r += '|{:=<12}|{:=<12}|\n'.format('','')
        self.console.writeOutput(r)

    def onBRelease(self,e):
        self.updateStatusbar(e)

    def onKRelease(self,e):
        self.updateStatusbar(e)

    def updateStatusbar(self,e):
        rcs = self.netlisteditor.index(INSERT)
        rc = rcs.split('.')
        self.statusbar.setPosition((rc[0],rc[1]))

if __name__ == '__main__':
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)
    ef = EditorFrame(root,'netlists/TRAN/FW_RECT.net')
    root.bind('<Control-q>', lambda e: root.quit)
    root.bind('<Control-r>', lambda e: ef.run_netlist)
    root.after(1000,ef.run_netlist)
    root.mainloop()
