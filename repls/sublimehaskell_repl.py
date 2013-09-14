import re
import os
import sublime

from .subprocess_repl import SubprocessRepl

def get_settings():
    return sublime.load_settings("SublimeHaskell.sublime-settings")

def get_setting(key, default=None):
    "This should be used only from main thread"
    # Get setting
    return get_settings().get(key, default)

def ghci_package_db():
    dev = get_setting('use_cabal_dev')
    box = get_setting('cabal_dev_sandbox')
    if dev and box:
        package_conf = (filter(lambda x: re.match('packages-(.*)\.conf', x), os.listdir(box)) + [None])[0]
        if package_conf:
            return os.path.join(box, package_conf)
    return None

def ghci_append_package_db(cmd):
    package_conf = ghci_package_db()
    if package_conf:
        cmd.extend(['-package-db', package_conf])
    return cmd

def ghci_get_min_whitespace_prefix(lines):
    line_spaces = [len(line) - len(line.lstrip()) for line in lines]
    if not line_spaces:
        return 0
    min_spaces = min(line_spaces)
    return min_spaces

def ghci_inject_let(lines):
    fixed_lines = [line for line in lines if not line.isspace()]

    letprefix =   "let "
    spaceprefix = "    "

    # matches eg. "func x y z ="
    # must start lowercase at start of line
    # remaining chars must be upper or lowercase letters, numbers, _ or '
    if fixed_lines and (not fixed_lines[0].startswith("let ")) and re.search("\A([a-z](\w|['_])*[ ]).*[=][ ]", lines[0]):
        fixed_lines[0] = letprefix + fixed_lines[0]
        fixed_lines[1:] = [spaceprefix + line for line in fixed_lines[1:]]

    return fixed_lines

def ghci_remove_whitespace(lines):
    # remove lines that are completely whitespace
    lines = [line for line in lines if not line.isspace()]

    # remove extra whitespace for more flexible block execution
    min_spaces = ghci_get_min_whitespace_prefix(lines)

    # remove the minimum number of spaces over all lines from each
    fixed_lines = [line[min_spaces:] for line in lines]
    return fixed_lines

def ghci_wrap_multiline_syntax(lines):
    # wrap in mutli-line syntax if more than one line
    if len(lines) <= 1:
        return lines
    fixed_lines = [":{" + os.linesep] + lines + [os.linesep + ":}" + os.linesep]
    return fixed_lines

class SublimeHaskellRepl(SubprocessRepl):
    TYPE = "sublime_haskell"

    def __init__(self, encoding, cmd=None, **kwds):
        super(SublimeHaskellRepl, self).__init__(encoding, cmd=ghci_append_package_db(cmd), **kwds)

    def write(self, command):
        setting_multiline = get_setting('format_multiline', True)
        setting_trimwhitespace = get_setting('format_trim_whitespace', True)
        setting_injectlet = get_setting('format_inject_let', True)

        new_cmd = ""
        if command.isspace() or (not setting_multiline and not setting_trimwhitespace):
            new_cmd = command
        else:
            lines = command.splitlines(True)
            if setting_trimwhitespace:
                lines = ghci_remove_whitespace(lines)
            if setting_injectlet:
                lines = ghci_inject_let(lines)
            if setting_multiline:
                lines = ghci_wrap_multiline_syntax(lines)
            new_cmd = "".join(lines)
        return super(SublimeHaskellRepl, self).write(new_cmd)
