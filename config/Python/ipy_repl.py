import os
activate_this = os.environ.get("SUBLIMEREPL_ACTIVATE_THIS", None)

if activate_this:
    with open(activate_this, "r") as f:
        exec(f.read(), {"__file__": activate_this})

try:
    import IPython
    IPYTHON = True
except ImportError:
    IPYTHON = False

## compatibility if no ipython available or running on windows
if not IPYTHON or os.name == "nt":
    import code
    code.InteractiveConsole().interact()

import sys
import json
import socket
import threading

from IPython.frontend.terminal.embed import InteractiveShellEmbed
from IPython.config.loader import Config


editor = "subl -w"

cfg = Config()
cfg.InteractiveShell.use_readline = False
cfg.InteractiveShell.autoindent = False
cfg.InteractiveShell.colors = "NoColor"
cfg.InteractiveShell.editor = os.environ.get("SUBLIMEREPL_EDITOR", editor)


from IPython.frontend.terminal.console.app import ZMQTerminalIPythonApp
from IPython.frontend.terminal.console.completer import ZMQCompleter

embedded_shell = ZMQTerminalIPythonApp(config=cfg, user_ns={})
embedded_shell.initialize()

# completer = ZMQCompleter(embedded_shell.shell, embedded_shell.kernel_manager)
#embedded_shell = InteractiveShellEmbed(config=cfg, user_ns={})

ac_port = int(os.environ.get("SUBLIMEREPL_AC_PORT", "0"))
ac_ip = os.environ.get("SUBLIMEREPL_AC_IP", "127.0.0.1")
if ac_port:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ac_ip, ac_port))


def read_netstring(s):
    size = 0
    while True:
        ch = s.recv(1)
        if ch == b':':
            break
        size = size * 10 + int(ch)
    msg = b""
    while size != 0:
        msg += s.recv(size)
        size -= len(msg)
    ch = s.recv(1)
    assert ch == b','
    return msg


def send_netstring(s, msg):
    payload = b"".join([str(len(msg)).encode("ascii"), b':', msg.encode("utf-8"), b','])
    s.sendall(payload)


def complete(zmq_shell, req):
    msg_id = zmq_shell.kernel_manager.shell_channel.complete(**req)
    msg = zmq_shell.kernel_manager.shell_channel.get_msg(timeout=0.5)
    if msg['parent_header']['msg_id'] == msg_id:
        return msg["content"]["matches"]
    return []

def handle():
    while True:
        msg = read_netstring(s).decode("utf-8")
        try:
            req = json.loads(msg)
            completions = complete(embedded_shell, req)
            result = (req["text"], completions)
            res = json.dumps(result)
            send_netstring(s, res)
        except Exceptione:
            send_netstring(s, b"[]")

if ac_port:
    t = threading.Thread(target=handle)
    t.start()

embedded_shell.start()

if ac_port:
    s.close()
