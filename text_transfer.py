from sublimerepl import find_repl
import sublime_plugin
import sublime
from collections import defaultdict
import tempfile


"""This is a bit stupid, but it's really difficult to create a temporary file with
a persistent name that can be passed to external process using this name, and then 
delete it reliably..."""
TEMP_FILE = None

def temp_file():
    global TEMP_FILE
    if not TEMP_FILE:
        TEMP_FILE = tempfile.NamedTemporaryFile(delete=False, prefix="SublimeREPL_")
        TEMP_FILE.close()
    return TEMP_FILE


def unload_handler():
    import os.path
    if not TEMP_FILE or not os.path.isfile(TEMP_FILE.name):
        return
    os.unlink(TEMP_FILE.name)

def default_sender(repl, text, file_name=None):
    repl.write(text)

"""Senders is a dict of functions used to transfer text to repl as a repl
   specific load_file action"""
SENDERS = defaultdict(lambda: default_sender)

def sender(external_id,):
    def wrap(func):
        SENDERS[external_id] = func
    return wrap

@sender("python")
def python_sender(repl, text, file_name=None):    
    import codecs
    tfile = temp_file()
    with codecs.open(tfile.name, "w", "utf-8") as tmp:
        tmp.write(text)
    repl.write('execfile(r"{0}")\n'.format(codecs.encode(tfile.name, "utf8")))


class ReplViewWrite(sublime_plugin.WindowCommand):
    def run(self, external_id, text, file_name=None):
        rv = find_repl(external_id)
        if not rv:
            return 
        rv.append_input_text(text)


class ReplSend(sublime_plugin.WindowCommand):
    def run(self, external_id, text, with_auto_postfix=True, file_name=None):
        rv = find_repl(external_id)
        if not rv:
            return 
        cmd = text
        if with_auto_postfix:
            cmd += rv.repl.cmd_postfix
        SENDERS[external_id](rv.repl, cmd, file_name)


class ReplTransferCurrent(sublime_plugin.TextCommand):
    def run(self, edit, scope="selection", action="send"):
        text = ""
        if scope == "selection":
            text = self.selected_text()
        elif scope == "lines":
            text = self.selected_lines()
        elif scope == "function":
            text = self.selected_functions()
        elif scope == "block":
            text = self.selected_blocks()
        elif scope == "file":
            text = self.selected_file()
        cmd = "repl_" + action
        self.view.window().run_command(cmd, {"external_id": self.repl_external_id(), "text": text, "file_name": self.view.file_name()})

    def repl_external_id(self):
        return self.view.scope_name(0).split(" ")[0].split(".")[1]

    def selected_text(self):
        v = self.view
        parts = [v.substr(region) for region in v.sel()]
        return "".join(parts)

    def selected_blocks(self):
        # TODO: Clojure only for now
        v = self.view
        strs = []
        old_sel = list(v.sel()) 
        v.run_command("expand_selection", {"to": "brackets"})
        v.run_command("expand_selection", {"to": "brackets"})
        for s in v.sel():
            strs.append(v.substr(s))
        v.sel().clear()
        for s in old_sel:
            v.sel().add(s)
        return "\n\n".join(strs)

    def selected_lines(self):
        v = self.view
        parts = []
        for sel in v.sel():
            for line in v.lines(sel):
                parts.append(v.substr(line))
        return "\n".join(parts)

    def selected_file(self):
        v = self.view
        return v.substr(sublime.Region(0, v.size()))