import code

if __name__ == '__main__':
    envVars = globals().copy()
    envVars.update(locals())
    shell = code.InteractiveConsole(envVars)
    shell.interact()
