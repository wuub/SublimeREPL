# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net) 
# All rights reserved. 
# See LICENSE.txt for details.

import subprocess
import os
import repl

class SubprocessRepl(repl.Repl):
    TYPE = "subprocess"

    def __init__(self, encoding, external_id=None, cmd_postfix="\n", suppress_echo=False, cmd=None, 
                 env=None, cwd=None, extend_env=None, soft_quit=""):
        super(SubprocessRepl, self).__init__(encoding, external_id, cmd_postfix, suppress_echo)
        self._cmd = cmd
        self._soft_quit = soft_quit
        self.popen = subprocess.Popen(
                        cmd, 
                        startupinfo=self.startupinfo(),
                        bufsize=1, 
                        cwd=self.cwd(cwd),
                        env=self.env(env, extend_env),
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE)

    def cwd(self, cwd):
        import os.path
        if cwd and os.path.exists(cwd):
            return cwd
        return None

    def env(self, env, extend_env):
        import os
        from sublime import load_settings
        updated_env = env if env else os.environ.copy()

        default_extend_env = load_settings('SublimeREPL.sublime-settings').get("default_extend_env")
        if default_extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, default_extend_env))

        if extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, extend_env))
        bytes_env = {}
        for k,v in updated_env.items():
            try:
                enc_k = self.encoder(unicode(k))[0]
                enc_v = self.encoder(unicode(v))[0]
            except UnicodeDecodeError:
                continue #f*** it, we'll do it live
            bytes_env[enc_k] = enc_v
        return bytes_env

    def interpolate_extend_env(self, env, extend_env):
        """Interpolates (subst) values in extend_env.
           Mostly for path manipulation"""
        new_env = {}
        for key, val in extend_env.items():
            new_env[key] = str(val).format(**env)
        return new_env

    def startupinfo(self):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return startupinfo

    def name(self):
        if self.external_id:
            return self.external_id
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
        self.write(self._soft_quit)
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

