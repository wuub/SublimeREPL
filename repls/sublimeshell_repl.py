import re

from .subprocess_repl import SubprocessRepl

class SublimeShellRepl(SubprocessRepl):
    TYPE = "sublime_shell"

    def __init__(self, encoding, cmd=None, **kwds):
        super(SublimeShellRepl, self).__init__(encoding, cmd=cmd, **kwds)

    def read(self):
        while True:
            bs = self.read_bytes()
            if not bs:
                return None

            try:
                # when opening Shell REPL -> errors are shown because the bash is not running in TTY
                # and therefore the terminal process group cannot be set:
                #       bash: cannot set terminal process group (10552): Inappropriate ioctl for device
                #       bash: no job control in this shell
                # This will surpress these errors
                bs = re.sub(b'bash:(.*?)(device|shell)\n', b'', bs)

                # Odd behaviour observed with the Primary Prompt String (PS1) of the bash
                # It contains PS1 twice and some hex cahracters at the begin/end of the first one \x1b and \x07
                #       b'\x1b]0;user@hostname: ~/.config/sublime-text-3/Packages/SublimeREPL/repls\x07user@hostname:~/.config/sublime-text-3/Packages/SublimeREPL/repls$ '    
                #Unfortunately I failed to find the reason for this behavior :( but the below regex substitution will )
                # remove the the first PS1 with the bex characters displaying just the standard PS1
                bs = re.sub(b"\x1b.*\x07", b'', bs)

                output = self.decoder.decode(bs)
            except Exception as e:
                output = "■"
                self.reset_decoder()

            if output:
                return output


