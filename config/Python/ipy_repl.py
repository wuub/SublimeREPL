import sys
import json
import socket
import threading

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

embedded_shell = InteractiveShellEmbed(config=cfg)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("localhost", 9999))
s.listen(1)

def handle():
    while True:
        clisock = s.accept()[0].makefile()
        req = json.loads(clisock.readline())
        completions = embedded_shell.complete(**req)
        clisock.write(json.dumps(completions) + "\n")
        clisock.close()

t = threading.Thread(target=handle)
t.start()

embedded_shell()
