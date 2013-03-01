import re
import os
import sublime
import sublime_plugin

import subprocess_repl

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

class SublimeHaskellRepl(subprocess_repl.SubprocessRepl):
    TYPE = "sublime_haskell"

    def __init__(self, encoding = None, external_id = None, cmd_postfix = "\n", suppress_echo = False, cmd = None, env = None, cwd = None, extend_env = None, soft_quit = "", autocomplete_server = False):
        super(SublimeHaskellRepl, self).__init__(encoding, external_id, cmd_postfix, suppress_echo, ghci_append_package_db(cmd), env, cwd, extend_env, soft_quit, autocomplete_server)
