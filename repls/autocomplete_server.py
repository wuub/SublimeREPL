# -*- coding: utf-8 -*-

import json
import socket
import threading
import sublime

def read_netstring(s):
    size = 0
    while True:
        ch = s.recv(1)
        if ch == ':':
            break
        size = size * 10 + int(ch)
    msg = ""
    while size != 0:
        msg += s.recv(size)
        size -= len(msg)
    ch = s.recv(1)
    assert ch == ','
    return msg

def send_netstring(s, msg):
    payload = "".join([str(len(msg)), ':', msg, ','])
    s.sendall(payload)


class AutocompleteServer(object):
    def __init__(self, repl):
        self._repl = repl
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._cli_sock = None

    def start(self):
        self._sock.bind(("localhost", 0))
        threading.Thread(target=self._wait).start()

    def _wait(self):
        self._sock.listen(1)
        s, address = self._sock.accept()
        print "accepted", address
        self._cli_sock = s
        print "thread end"

    def port(self):
        return self._sock.getsockname()[1]

    def connected(self):
        return bool(self._cli_sock)

    def complete(self, whole_line, pos_in_line, prefix, whole_prefix, locations):
        text = whole_prefix
        for ch in [' ', '(', ',']:
            text_parts = text.rsplit(ch, 1)
            text = text_parts.pop()

        req = json.dumps({"text": "", "line": whole_line, "cursor_pos": pos_in_line})
        # req = json.dumps({"text": text, "line": whole_line})
        send_netstring(self._cli_sock, req)
        msg = read_netstring(self._cli_sock)
        res = json.loads(msg)
        return [(x, x) for x in res[1]]

    def __del__(self):
        print "on del"


        #
        # print view, prefix, locations, whole_prefix
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.settimeout(5.0)
        # s.connect(("localhost", 9999))
        # try:
            # TODO: split
            # text = whole_prefix
            # for ch in [' ', '(', ',']:
                # text_parts = text.rsplit(ch, 1)
                # text = text_parts.pop()
            # s.sendall(json.dumps({"line": whole_prefix, "text": text, "cursor_pos": len(whole_prefix)}) + "\n")
            # res = json.loads(s.recv(65535))
        # finally:
            # s.close()
#
        # comp = [(x,x) for x in res[1]]
        # return (comp, flags)
#
