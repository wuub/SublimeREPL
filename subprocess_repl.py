# -*- coding: utf-8 -*-

import subprocess
import os
import repl

class SubprocessRepl(repl.Repl):
    def __init__(self, encoding, cmd, **kwds):
        super(SubprocessRepl, self).__init__(encoding)
        self._cmd = cmd
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.popen = subprocess.Popen(
                        cmd, 
                        startupinfo=startupinfo,
                        bufsize=1, 
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        **kwds)

    def name(self):
        if isinstance(self._cmd, basestring):
            return self._cmd
        return " ".join([str(x) for x in self._cmd])

    def is_alive(self):
        return self.popen.poll() is None

    def read_bytes(self):
        # this is windows specific problem, that you cannot tell if there 
        # are more bytes ready, so we read only 1 at a times
        return self.popen.stdout.read(1)

    def write_bytes(self, bytes):
        si = self.popen.stdin 
        si.write(bytes)
        si.flush()

    def kill(self):
        self.popen.kill()
