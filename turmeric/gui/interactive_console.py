#import code
from traitlets.config import Config
import IPython
from IPython.terminal.prompts import Prompts, Token

class NoNumberPrompt(Prompts):

    def out_prompt_tokens(self):
        return [(Token.Prompt, '')]

    def in_prompt_tokens(self, cli=None):
        return [(Token.Prompt, '$ ')]


if __name__ == '__main__':
    c = Config()
    c.InteractiveShellApp.exec_lines = [
            'from turmeric import runnet',
            'import pickle',
            #'from IPython import display',
            #'%gui tk',
            #'%matplotlib tk'
            ]
    c.InteractiveShellApp.exec_files = [

            ]
    c.InteractiveShell.colors = 'LightBG'
    c.InteractiveShell.confirm_exit = False
    c.TerminalIPythonApp.display_banner = False
#    c.TerminalInteractiveShell.prompts_class = NoNumberPrompt
    IPython.start_ipython(config=c)
