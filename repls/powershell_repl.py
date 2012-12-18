# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.

import subprocess
import os
import re
import repl
import signal
import killableprocess
from sublime import load_settings
from autocomplete_server import AutocompleteServer

from subprocess_repl import Unsupported, win_find_executable
import subprocess_repl

class PowershellRepl(subprocess_repl.SubprocessRepl):
    TYPE = "powershell"

    def __init__(self, encoding = None, external_id=None, cmd_postfix="\n", suppress_echo=False, cmd=None,
                 env=None, cwd=None, extend_env=None, soft_quit="", autocomplete_server=False):
        if not encoding:
            # Detect encoding
            chcp = os.popen('chcp')
            chcp_encoding = re.match(r'[^\d]+(\d+)$', chcp.read())
            if not chcp_encoding:
                raise LookupError("Can't detect encoding from chcp")
            encoding = "cp" + chcp_encoding.groups()[0]
            print(encoding)

        super(PowershellRepl, self).__init__(encoding, external_id, cmd_postfix, suppress_echo, cmd, env, cwd, extend_env, soft_quit, autocomplete_server)

        self.prompt()

    # def read_bytes(self):
    #     # this is windows specific problem, that you cannot tell if there
    #     # are more bytes ready, so we read only 1 at a times
    #     return self.popen.stdout.read(1)

    def write_bytes(self, bytes):
        super(PowershellRepl, self).write_bytes(bytes)
        self.prompt()

    def prompt(self):
        si = self.popen.stdin
        si.write('Write-Host ("PS " + (gl).Path + "> ") -NoNewline\n')
        si.flush()
