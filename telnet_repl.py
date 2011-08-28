# -*- coding: utf-8 -*-

import telnetlib
import repl

class TelnetRepl(repl.Repl):
    def __init__(self, encoding, external_id=None, host="localhost", port=23, cmd_postfix=None):
        super(TelnetRepl, self).__init__(encoding, external_id)
        self._telnet = telnetlib.Telnet()
        self._telnet.open(host, int(port))
        self._alive = True
        self._cmd_postfix = cmd_postfix

    def name(self):
        return "%s:%s" % (self._telnet.host, self._telnet.port)

    def is_alive(self):
        return self._alive

    def read_bytes(self):
        return self._telnet.read_some()

    def write_bytes(self, bytes):
        self._telnet.write(bytes)
        if self._cmd_postfix:
            self._telnet.write(self.encoder(self._cmd_postfix)[0])

    def kill(self):
        self._telnet.close()
        self._alive = False
