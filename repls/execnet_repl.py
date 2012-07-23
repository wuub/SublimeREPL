# encoding: utf-8
import repl
from Queue import Queue
import sys
import execnet

remote = """
import code
import sys
import contextlib
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
        self.output = channel
        self.output.send(self.PS1)

    def write(self, data):
        self.output.send(data)

    def push(self, line):
        from StringIO import StringIO
        s = StringIO()
        with redirect_stdio(s):
            more = code.InteractiveConsole.push(self, line)
        if s.len:
            self.output.send(s.getvalue())
        self.output.send(self.PS2 if more else self.PS1)
        return more

ic = InterceptingConsole()
while not channel.isclosed():
    param = channel.receive()
    ic.push(param)
"""

class ExecnetRepl(repl.Repl):
    TYPE = "execnet_repl"

    def __init__(self, encoding):
        super(ExecnetRepl, self).__init__(encoding, u"python", "\n", False)
        self._gw = execnet.makegateway("popen//python=C:\\Python27\\pythonw.exe")
        self._channel = self._gw.remote_exec(remote)
        self.output = Queue()
        self._channel.setcallback(self.output.put, endmarker=None)
        self._alive = True
        self._killed = False

    def name(self):
        return "execnet"

    def is_alive(self):
        return self._alive

    def write_bytes(self, bytes):
        if self._channel.isclosed():
            self._alive = False
        else:
            self._channel.send(bytes)
        
    def read_bytes(self):
        bytes = self.output.get()
        if bytes is None:
            self._gw.exit()
        else:
            return bytes

    def kill(self):
        self._killed = True
        self._gw.exit()