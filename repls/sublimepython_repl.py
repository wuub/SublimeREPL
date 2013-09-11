# encoding: utf-8
import code
import contextlib
from .repl import Repl
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import sys
import threading
import sublime


class QueueOut(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, data):
        self.queue.put(data)


@contextlib.contextmanager
def redirect_stdio(queue):
    orig = (sys.stdout, sys.stderr)
    sys.stdout = sys.stderr = QueueOut(queue)
    yield
    (sys.stdout, sys.stderr) = orig


class SublimeLocals(dict):
    def __init__(self, *args, **kwds):
        import pydoc
        super(SublimeLocals, self).__init__(*args, **kwds)
        self['sublime'] = sublime
        self['__name__'] = "__main__"
        self['view'] = None
        self['window'] = None
        self['help'] = pydoc.help

    def __getitem__(self, key):
        if key == 'window':
            return sublime.active_window()
        if key == 'view':
            return sublime.active_window().active_view()
        return super(SublimeLocals, self).__getitem__(key)


class InterceptingConsole(code.InteractiveConsole):
    PS1 = ">>> "
    PS2 = "... "

    def __init__(self, encoding):
        code.InteractiveConsole.__init__(self, locals=SublimeLocals())
        self.input = Queue()
        self.output = Queue()
        self.output.put(self.PS1)
        self._encoding = encoding

    def write(self, data):
        self.output.put(data)

    def push(self, line):
        with redirect_stdio(self.output):
            more = code.InteractiveConsole.push(self, line.decode(self._encoding))
        self.output.put(self.PS2 if more else self.PS1)
        return more

    def run(self):
        while True:
            line = self.input.get()
            if line is None:
                break
            self.push(line)


class SublimePythonRepl(Repl):
    TYPE = "sublime_python"

    def __init__(self, encoding):
        super(SublimePythonRepl, self).__init__(encoding, "python", "\n", False)
        self._console = InterceptingConsole(encoding)
        self._thread = threading.Thread(target=self._console.run)
        self._thread.start()

    def name(self):
        return "sublime"

    def is_alive(self):
        return True

    def write_bytes(self, bytes):
        self._console.input.put(bytes)

    def read_bytes(self):
        return self._console.output.get().encode(self._encoding)

    def kill(self):
        self._console.input.put(None)
