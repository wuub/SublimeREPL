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

def removeWhitespace(lines):
    # remove lines that are completely whitespace
    lines = [line for line in lines if not line.isspace()]
    
    # remove extra whitespace for more flexible block execution        
    lineSpaces = [len(line) - len(line.lstrip()) for line in lines]
    minSpaces = min(lineSpaces)
    fixedLines = [line[minSpaces:] for line in lines]
    return fixedLines

def wrapMultilineSyntax(lines):
    # append mutli-line syntax if more than one line
    lineLen = len(lines)
    fixedLines = lines + [os.linesep] if lineLen == 1 else [":{" + os.linesep] + lines + [os.linesep + ":}" + os.linesep]
    return fixedLines

class SublimeHaskellRepl(SubprocessRepl):
    TYPE = "sublime_haskell"

    def __init__(self, encoding, cmd=None, **kwds):
        super(SublimeHaskellRepl, self).__init__(encoding, cmd=ghci_append_package_db(cmd), **kwds)

    def write(self, command):
        setting_multiline = get_setting('format_multiline', False)
        setting_trimwhitespace = get_setting('format_trim_whitespace', False)
        
        newCmd = ""
        if command.isspace() or (not setting_multiline and not setting_trimwhitespace):
                newCmd = command
        else:
                lines = command.splitlines(True)
                if setting_trimwhitespace:
                        lines = removeWhitespace(lines)
                if setting_multiline:
                        lines = wrapMultilineSyntax(lines)
                newCmd = "".join(lines)

	return super(HaskellRepl, self).write(newCmd)
