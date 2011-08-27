# -*- coding: utf-8 -*-

import telnetlib
import repl

class TelnetRepl(repl.Repl):
    def __init__(self, encoding, host="localhost", port=23):
        super(TelnetRepl, self).__init__(encoding)
        self._telnet = telnetlib.Telnet()
        self._telnet.open(host, int(port))
        self._alive = True

    def name(self):
        return "%s:%s" % (self._telnet.host, self._telnet.port)

    def is_alive(self):
        return self._alive

    def read_bytes(self):
        return self._telnet.read_some()

    def write_bytes(self, bytes):
        self._telnet.write(bytes)

    def kill(self):
        self._telnet.close()
        self._alive = False
