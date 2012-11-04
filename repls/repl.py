# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.

from autocomplete_server import AutocompleteServer
from uuid import uuid4
from codecs import getincrementaldecoder, getencoder


class NoReplError(LookupError):
    """Looking for Repl subclass failed"""
    pass

class Repl(object):
    """Class that represents a process that is being executed.
       For example this can be python, bash or a telnet session"""

    TYPE = "<base>"

    @classmethod
    def subclass(cls, type):
        """Returns subclass of Repl of given type eq. SubprocessRepl"""
        todo = [cls]
        seen = set()
        while True:
            if not todo:
                raise NoReplError
            cur = todo.pop()
            if cur in seen:
                continue
            if cur.TYPE == type:
                return cur
            todo.extend(cur.__subclasses__())

    def __init__(self, encoding, external_id=None, cmd_postfix="\n", suppress_echo=False, autocomplete_server=False):
        self.id = uuid4().hex
        self.decoder = getincrementaldecoder(encoding)()
        self.encoder = getencoder(encoding)
        self.external_id = external_id
        self.cmd_postfix = cmd_postfix
        self.suppress_echo = suppress_echo

        self._autocomplete_server = None
        if autocomplete_server:
            self._autocomplete_server = AutocompleteServer(self)
            self._autocomplete_server.start()

    def autocomplete_server_port(self):
        if not self._autocomplete_server:
            return None
        return self._autocomplete_server.port()

    def autocomplete_available(self):
        return self._autocomplete_server.connected()

    def autocomplete_completions(self, whole_line, pos_in_line, prefix, whole_prefix, locations):
        return self._autocomplete_server.complete(
            whole_line=whole_line,
            pos_in_line=pos_in_line,
            prefix=prefix,
            whole_prefix=whole_prefix,
            locations=locations,
        )

    def close(self):
        if self.is_alive():
            self.kill()

    def name(self):
        """Returns name of this repl that should be used as a filename"""
        return NotImplementedError

    def is_alive(self):
        """ Returns true if the undelying process is stil working"""
        raise NotImplementedError

    def write_bytes(self, bytes):
        raise NotImplementedError

    def read_bytes(self):
        """Reads at lest one byte of Repl output. Returns None if output died.
           Can block!!!"""
        raise NotImplementedError

    def kill(self):
        """Kills the underlying repl"""
        raise NotImplementedError

    def write(self, command):
        """Encodes and evaluates a given command"""
        (bytes, how_many) = self.encoder(command)
        return self.write_bytes(bytes)

    def read(self):
        """Reads at least one decoded char of output"""
        while True:
            bs = self.read_bytes()
            if not bs:
                return None
            try:
                output = self.decoder.decode(bs)
            except Exception, e:
                output = "[SublimeRepl: decode error]\n"
            if output:
                return output
