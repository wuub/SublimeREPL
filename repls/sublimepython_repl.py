# encoding: utf-8
import code
import contextlib
import repl
from Queue import Queue
import sys

@contextlib.contextmanager
def redirect_stdio(sio):
    orig = (sys.stdout, sys.stderr)
    sys.stdout = sys.stderr = sio
    yield
    (sys.stdout, sys.stderr) = orig

class InterceptingConsole(code.InteractiveConsole):
    PS1 = ">>> "
    PS2 = "... "
    def __init__(self, *args, **kwds):
        code.InteractiveConsole.__init__(self, *args, **kwds)
        self.output = Queue()
        self.output.put(self.PS1)

    def write(self, data):
        self.output.put(data)

    def push(self, line):
        from StringIO import StringIO
        s = StringIO()
        with redirect_stdio(s):
            more = code.InteractiveConsole.push(self, line)
        if s.len:
            self.output.put(s.getvalue())
        self.output.put(self.PS2 if more else self.PS1)
        return more


class SublimePythonRepl(repl.Repl):
    TYPE = "sublime_python"

    def __init__(self, encoding):
        super(SublimePythonRepl, self).__init__(encoding, u"python", "\n", False)
        self._console = InterceptingConsole()

    def name(self):
        return "sublime"

    def is_alive(self):
        return True

    def write_bytes(self, bytes):
        self._console.push(bytes)
        
    def read_bytes(self):
        return self._console.output.get()

    def kill(self):
        pass