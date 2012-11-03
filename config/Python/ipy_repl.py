import sys
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

embedded_shell()
