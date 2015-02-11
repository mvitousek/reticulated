from . import flags

def warn(msg, priority):
    if flags.WARNINGS >= priority:
        print('WARNING:', msg)    

def debug(msg, mode):
    if isinstance(mode, int):
        mode = [mode]
    mode = [m for m in mode if m in flags.DEBUG_MODES]
    if flags.DEBUG_MESSAGES and mode:
        print('DEBUG (%s): %s' % (flags.DEBUG_MODE_NAMES[mode[0]], msg))
