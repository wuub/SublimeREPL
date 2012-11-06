import sys
import json
import socket
import threading
import os

from IPython.frontend.terminal.embed import InteractiveShellEmbed
from IPython.config.loader import Config


editor = "subl -w"
if len(sys.argv) > 1:
    editor = sys.argv[1]

cfg = Config()
cfg.InteractiveShell.use_readline = False
cfg.InteractiveShell.autoindent = False
cfg.InteractiveShell.colors = "NoColor"
cfg.InteractiveShell.editor = editor


embedded_shell = InteractiveShellEmbed(config=cfg, user_ns={})

ac_port = int(os.environ.get("SUBLIMEREPL_AC_PORT", "0"))
if ac_port:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", ac_port))


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


def handle():
    while True:
        msg = read_netstring(s)
        try:
            req = json.loads(msg)
            completions = embedded_shell.complete(**req)
            res = json.dumps(completions)
            send_netstring(s, res)
        except:
            send_netstring(s, "[]")

if ac_port:
    t = threading.Thread(target=handle)
    t.start()

embedded_shell()

if ac_port:
    s.close()
