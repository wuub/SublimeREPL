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

class SublimeHaskellRepl(SubprocessRepl):
    TYPE = "sublime_haskell"

    def __init__(self, encoding, cmd=None, **kwds):
        super(SublimeHaskellRepl, self).__init__(encoding, cmd=ghci_append_package_db(cmd), **kwds)
