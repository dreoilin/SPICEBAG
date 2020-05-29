#import code
from traitlets.config import Config
import IPython

if __name__ == '__main__':
    c = Config()
    c.InteractiveShellApp.exec_lines = [
            'from turmeric import runnet'
            ]
    c.InteractiveShellApp.exec_files = [

            ]
    c.InteractiveShell.colors = 'LightBG'
    c.InteractiveShell.confirm_exit = False
    c.TerminalIPythonApp.display_banner = False
    IPython.start_ipython(config=c)
