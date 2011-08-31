# -*- coding: utf-8 -*-

import subprocess
import os
import repl

class SubprocessRepl(repl.Repl):
    TYPE = "subprocess"

    def __init__(self, encoding, external_id=None, cmd=None, env=None, cwd=None, env_extension=None):
        super(SubprocessRepl, self).__init__(encoding, external_id)
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
                        stdout=subprocess.PIPE)

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

    def available_signals(self):
        import signal
        signals = {}
        for k, v in signal.__dict__.items():
            if not k.startswith("SIG"):
                continue
            signals[k] = v
        return signals

    def send_signal(self, signal):
        if self.is_alive():
            self.popen.send_signal(signal)

