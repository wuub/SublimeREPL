# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.
from __future__ import absolute_import, unicode_literals, print_function, division

import subprocess
import os
import sys
from .repl import Repl
import signal
from sublime import load_settings, error_message
from .autocomplete_server import AutocompleteServer
from .killableprocess import Popen

PY3 = sys.version_info[0] == 3

if os.name == 'posix':
    POSIX = True
    import fcntl
    import select
else:
    POSIX = False


class Unsupported(Exception):
    def __init__(self, msgs):
        super(Unsupported, self).__init__()
        self.msgs = msgs

    def __repr__(self):
        return "\n".join(self.msgs)


def win_find_executable(executable, env):
    """Explicetely looks for executable in env["PATH"]"""
    if os.path.dirname(executable):
        return executable # executable is already absolute filepath
    path = env.get("PATH", "")
    pathext = env.get("PATHEXT") or ".EXE"
    dirs = path.split(os.path.pathsep)
    (base, ext) = os.path.splitext(executable)
    if ext:
        extensions = [ext]
    else:
        extensions = pathext.split(os.path.pathsep)
    for directory in dirs:
        for extension in extensions:
            filepath = os.path.join(directory, base + extension)
            if os.path.exists(filepath):
                return filepath
    return None


class SubprocessRepl(Repl):
    TYPE = "subprocess"

    def __init__(self, encoding, cmd=None, env=None, cwd=None, extend_env=None, soft_quit="", autocomplete_server=False, **kwds):
        super(SubprocessRepl, self).__init__(encoding, **kwds)
        settings = load_settings('SublimeREPL.sublime-settings')

        if cmd[0] == "[unsupported]":
            raise Unsupported(cmd[1:])

        self._autocomplete_server = None
        if autocomplete_server:
            self._autocomplete_server = AutocompleteServer(self, settings.get("autocomplete_server_ip"))
            self._autocomplete_server.start()

        env = self.env(env, extend_env, settings)
        env[b"SUBLIMEREPL_AC_PORT"] = str(self.autocomplete_server_port()).encode("utf-8")
        env[b"SUBLIMEREPL_AC_IP"] = settings.get("autocomplete_server_ip").encode("utf-8")

        if PY3:
            strings_env = {}
            for k, v in env.items():
                strings_env[k.decode("utf-8")] = v.decode("utf-8")
            env = strings_env

        self._cmd = self.cmd(cmd, env)
        self._soft_quit = soft_quit
        self._killed = False
        self.popen = Popen(
                        self._cmd,
                        startupinfo=self.startupinfo(settings),
                        creationflags=self.creationflags(settings),
                        bufsize=1,
                        cwd=self.cwd(cwd, settings),
                        env=env,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE)

        if POSIX:
            flags = fcntl.fcntl(self.popen.stdout, fcntl.F_GETFL)
            fcntl.fcntl(self.popen.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def autocomplete_server_port(self):
        if not self._autocomplete_server:
            return None
        return self._autocomplete_server.port()

    def autocomplete_available(self):
        if not self._autocomplete_server:
            return False
        return self._autocomplete_server.connected()

    def autocomplete_completions(self, whole_line, pos_in_line, prefix, whole_prefix, locations):
        return self._autocomplete_server.complete(
            whole_line=whole_line,
            pos_in_line=pos_in_line,
            prefix=prefix,
            whole_prefix=whole_prefix,
            locations=locations,
        )

    def cmd(self, cmd, env):
        """On Linux and OSX just returns cmd, on windows it has to find
           executable in env because of this: http://bugs.python.org/issue8557"""
        if os.name != "nt":
            return cmd
        if isinstance(cmd, str):
            _cmd = [cmd]
        else:
            _cmd = cmd
        executable = win_find_executable(_cmd[0], env)
        if executable:
            _cmd[0] = executable
        return _cmd

    def cwd(self, cwd, settings):
        if cwd and os.path.exists(cwd):
            return cwd
        return None

    def getenv(self, settings):
        """Tries to get most appropriate environent, on windows
           it's os.environ.copy, but on other system's we'll
           try get values from login shell"""

        getenv_command = settings.get("getenv_command")
        if getenv_command and POSIX:
            try:
                output = subprocess.check_output(getenv_command)
                lines = output.decode("utf-8", errors="replace").splitlines()
                env = dict(line.split('=', 1)  for line in lines)
                return env
            except:
                import traceback
                traceback.print_exc()
                error_message(
                    "SublimeREPL: obtaining sane environment failed in getenv()\n"
                    "Check console and 'getenv_command' setting \n"
                    "WARN: Falling back to SublimeText environment")

        # Fallback to environ.copy() if not on POSIX or sane getenv failed
        return os.environ.copy()

    def env(self, env, extend_env, settings):
        updated_env = env if env else self.getenv(settings)
        default_extend_env = settings.get("default_extend_env")
        if default_extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, default_extend_env))
        if extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, extend_env))

        bytes_env = {}
        for k, v in list(updated_env.items()):
            try:
                enc_k = self.encoder(str(k))[0]
                enc_v = self.encoder(str(v))[0]
            except UnicodeDecodeError:
                continue #f*** it, we'll do it live
            else:
                bytes_env[enc_k] = enc_v
        return bytes_env

    def interpolate_extend_env(self, env, extend_env):
        """Interpolates (subst) values in extend_env.
           Mostly for path manipulation"""
        new_env = {}
        for key, val in list(extend_env.items()):
            new_env[key] = str(val).format(**env)
        return new_env

    def startupinfo(self, settings):
        startupinfo = None
        if os.name == 'nt':
            from .killableprocess import STARTUPINFO, STARTF_USESHOWWINDOW
            startupinfo = STARTUPINFO()
            startupinfo.dwFlags |= STARTF_USESHOWWINDOW
            startupinfo.wShowWindow |= 1 # SW_SHOWNORMAL
        return startupinfo

    def creationflags(self, settings):
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x8000000 # CREATE_NO_WINDOW
        return creationflags

    def name(self):
        if self.external_id:
            return self.external_id
        if isinstance(self._cmd, str):
            return self._cmd
        return " ".join([str(x) for x in self._cmd])

    def is_alive(self):
        return self.popen.poll() is None

    def read_bytes(self):
        out = self.popen.stdout
        if POSIX:
            while True:
                i, _, _ = select.select([out], [], [])
                if i:
                    return out.read(4096)
        else:
            # this is windows specific problem, that you cannot tell if there
            # are more bytes ready, so we read only 1 at a times

            while True:
                byte = self.popen.stdout.read(1)
                if byte == b'\r':
                    # f'in HACK, for \r\n -> \n translation on windows
                    # I tried universal_endlines but it was pain and misery! :'(
                    continue
                return byte



    def write_bytes(self, bytes):
        si = self.popen.stdin
        si.write(bytes)
        si.flush()

    def kill(self):
        self._killed = True
        self.write(self._soft_quit)
        self.popen.kill()

    def available_signals(self):
        signals = {}
        for k, v in list(signal.__dict__.items()):
            if not k.startswith("SIG"):
                continue
            signals[k] = v
        return signals

    def send_signal(self, sig):
        if sig == signal.SIGTERM:
            self._killed = True
        if self.is_alive():
            self.popen.send_signal(sig)

