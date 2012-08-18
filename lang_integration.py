import sublime
import sublime_plugin

import re
import os.path
import socket
from functools import partial

SETTINGS_FILE = "SublimeREPL.sublime-settings"

class ClojureAutoTelnetRepl(sublime_plugin.WindowCommand):
    def is_running(self, port_str):
        """Check if port is open on localhost"""
        port = int(port_str)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        return res == 0

    def choices(self):
        choices = []
        for folder in self.window.folders():
            proj_file = os.path.join(folder, "project.clj")
            try:
                with open(proj_file) as f:
                    data = f.read()
                    port_match = re.search(":repl-port\s+(\d{1,})", data)
                    if not port_match:
                        continue
                    port = port_match.group(1)
                    description = proj_file
                    desc_match = re.search(r':description\s+"([^"]+)"', data)
                    if desc_match:
                        description = desc_match.group(1)
                    if self.is_running(port):
                        description += " (active)"
                    else:
                        description += " (not responding)"
                    choices.append([description, port])
            except IOError, e:
                pass  # just ignore it, no file or no access

        return choices + [["Custom telnet", "Pick your own telnet port number to Lein REPL"]]

    def run(self):
        choices = self.choices()
        if len(choices) == 1: #only custom telnet action
            self.on_done(choices, 0)
        else:
            on_done = partial(self.on_done, choices)
            self.window.show_quick_panel(self.choices(), on_done)

    def on_done(self, choices, index):
        if index == -1:
            return
        if index == len(choices) - 1:
            self.window.show_input_panel("Enter port number", "",
                                         self.open_telnet_repl,
                                         None, None)
            return
        self.open_telnet_repl(choices[index][1])

    def open_telnet_repl(self, port_str):
        try:
            port = int(port_str)
        except ValueError:
            return
        self.window.run_command("repl_open", {"type":"telnet", "encoding":"utf8", "host":"localhost", "port":port,
                                "external_id":"clojure", "syntax":"Packages/Clojure/Clojure.tmLanguage"})


class PythonVirtualenvRepl(sublime_plugin.WindowCommand):
    def _scan(self):
        import os.path
        venv_paths = sublime.load_settings(SETTINGS_FILE).get("python_virtualenv_paths", [])
        found_dirs = set()
        for venv_path in venv_paths:
            for (directory, _, filenames) in os.walk(os.path.expanduser(venv_path)) :
                if "activate_this.py" in filenames:
                    found_dirs.add(directory)
        return sorted(found_dirs)

    def run_virtualenv(self, choices, index):
        if index == -1:
            return
        (name, directory) = choices[index]
        activate_file = os.path.join(directory, "activate_this.py")

        init_cmd = "execfile('{activate_file}', dict(__file__='{activate_file}')); import site; import sys; sys.ps1 = '({name}) >>> '; del sys;".format(name=name, activate_file=activate_file)
        self.window.run_command("repl_open",
            {
                "type":"telnet",
                "encoding":"utf8",
                "type": "subprocess",
                "extend_env": {"PATH": directory},
                "cmd": ["python", "-i", "-u", "-c", init_cmd],
                "cwd": "$file_path",
                "encoding": "utf8",
                "syntax": "Packages/Python/Python.tmLanguage",
                "external_id": "python"
             })

    def run(self):
        choices = self._scan()
        nice_choices = [[path.split(os.path.sep)[-2], path] for path in choices]
        self.window.show_quick_panel(nice_choices, partial(self.run_virtualenv, nice_choices))
