import sublime
import sublime_plugin

import re
import os.path
import socket
from functools import partial
from contextlib import closing

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


def scan_for_virtualenvs(venv_paths):
    import os.path
    found_dirs = set()
    for venv_path in venv_paths:
        for (directory, _, filenames) in os.walk(os.path.expanduser(venv_path)) :
            if "activate_this.py" in filenames:
                found_dirs.add(directory)
    return sorted(found_dirs)


class PythonVirtualenvRepl(sublime_plugin.WindowCommand):
    def _scan(self):
        venv_paths = sublime.load_settings(SETTINGS_FILE).get("python_virtualenv_paths", [])
        return scan_for_virtualenvs(venv_paths)

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


VENV_SCAN_CODE = """
import os.path

venv_paths = channel.receive()
found_dirs = set()
for venv_path in venv_paths:
    for (directory, _, filenames) in os.walk(os.path.expanduser(venv_path)) :
        if "activate_this.py" in filenames:
            found_dirs.add(directory)

channel.send(found_dirs)
channel.close()

"""

class ExecnetVirtualenvRepl(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel("SSH connection (eg. user@host)", "", self.on_ssh_select, None, None)

    def on_ssh_select(self, host_string):
        import execnet
        venv_paths = sublime.load_settings(SETTINGS_FILE).get("python_virtualenv_paths", [])
        gw = execnet.makegateway("ssh=" + host_string)
        ch = gw.remote_exec(VENV_SCAN_CODE)
        with closing(ch):
            ch.send(venv_paths)
            directories = ch.receive(10)
        gw.exit()

        choices = [[host_string + ":" + path.split(os.path.sep)[-2], path] for path in sorted(directories)]
        nice_choices = [["w/o venv", "n/a"]] + choices
        self.window.show_quick_panel(nice_choices, partial(self.run_virtualenv, host_string, nice_choices))

    def run_virtualenv(self, host_string, nice_choices, index):
        if index == -1:
            return
        if index == 0:
            connection_string = "ssh={host}".format(host=host_string)
            ps1 = "({host}@) >>> ".format(host=host_string)
            activate_file = ""
        else:
            (name, directory) = nice_choices[index]
            activate_file = os.path.join(directory, "activate_this.py")
            python_file = os.path.join(directory, "python")
            ps1 = "({name}) >>> ".format(name=name, host=host_string)
            connection_string = "ssh={host}//env:PATH={dir}//python={python}".format(
                host=host_string,
                dir=directory,
                python=python_file
            )

        self.window.run_command("repl_open",
                 {
                  "type": "execnet_repl",
                  "encoding": "utf8",
                  "syntax": "Packages/Python/Python.tmLanguage",
                  "connection_string": connection_string,
                  "activate_file": activate_file,
                  "ps1": ps1
                 })





