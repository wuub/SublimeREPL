# -*- coding: utf-8 -*-

import threading
import Queue
import sublime
import sublime_plugin
import repl

repl_views = {}

def repl_view(view):
    id = view.settings().get("repl_id")
    if not repl_views.has_key(id):
        return None
    rv = repl_views[id]
    rv.update_view(view)
    return rv


class ReplReader(threading.Thread):
    def __init__(self, repl):
        super(ReplReader, self).__init__()
        self.repl = repl
        self.daemon = True
        self.queue = Queue.Queue()

    def run(self):
        r = self.repl
        q = self.queue
        while True:
            result = r.read()
            q.put(result)
            if result is None:
                break
        print("Reader exiting")


class HistoryMatchList(object):
    def __init__(self, command_prefix, commands):
        self._command_prefix = command_prefix
        self._commands = commands
        self._cur = len(commands) # no '-1' on purpose

    def current_command(self):
        if not self._commands:
            return ""
        return self._commands[self._cur]

    def prev_command(self):
        self._cur = max(0, self._cur - 1)
        return self.current_command()

    def next_command(self):
        self._cur = min(len(self._commands) -1, self._cur + 1)
        return self.current_command()


class History(object):
    def __init__(self):
        self._stack = []

    def push(self, command):
        cmd = command.rstrip()
        if not cmd:
            return
        self._stack.append(cmd)

    def match(self, command_prefix):
        matching_commands = []
        for cmd in self._stack:
            if cmd.startswith(command_prefix):
                matching_commands.append(cmd)
        return HistoryMatchList(command_prefix, matching_commands)

class ReplView(object):
    def __init__(self, view, repl, syntax):
        view.settings().set("repl_id", repl.id)
        view.settings().set("repl", True)
        self.repl = repl
        self._view = view
        if syntax:
            view.set_syntax_file(syntax)
        self._output_end = view.size()
        self.view_init()
        self._repl_reader = ReplReader(repl)
        self._repl_reader.start()
        self._history = History()
        self._history_match = None
        # begin refreshing attached view
        self.update_view_loop()

    def view_init(self):
        from srlic import verify_license
        lic = sublime.load_settings("Global.sublime-settings").get("sublimerepl_license")
        (ok, licensee) = verify_license(lic)
        if ok:
            self.write("SublimeREPL Licenced to: %s\n" % (licensee,))
        else:
            self.write("!!! SublimeREPL - for evaluation and Non-Commercial use only !!!\n")


    def update_view(self, view):
        """If projects were switched, a view could be a new instance"""
        if self._view is not view:
            self._view = view

    def user_input(self):
        """Returns text entered by the user"""
        region = sublime.Region(self._output_end, self._view.size())
        return self._view.substr(region)

    def adjust_end(self):
        self._output_end = self._view.size()

    def write(self, unistr):
        """Writes output from Repl into this view."""
        # string is assumet to be already correctly encoded
        v = self._view
        edit = v.begin_edit()
        try:
            v.insert(edit, self._output_end, unistr)
            self._output_end += len(unistr)
        finally:
            v.end_edit(edit)
        self.scroll_to_end()

    def scroll_to_end(self):
        v = self._view
        v.show(v.line(v.size()).begin())

    def new_output(self):
        """Returns new data from Repl and bool indicating if Repl is still 
           working"""
        q = self._repl_reader.queue
        data = ""
        try:
            while True:
                packet = q.get_nowait()
                if packet is None:
                    return data, False
                data += packet
        except Queue.Empty:
            return data, True

    def update_view_loop(self):
        (data, is_still_working) = self.new_output()
        if data:
            self.write(data)
        if is_still_working:
            sublime.set_timeout(self.update_view_loop, 100)
        else:
            self.write("\n***Repl Closed***\n""")
            self._view.set_read_only(True)
            
    def push_history(self, command):
        self._history.push(command)
        self._history_match = None

    def ensure_history_match(self):
        user_input = self.user_input()
        if self._history_match is not None:
            if user_input != self._history_match.current_command():
                # user did something! reset
                self._history_match = None
        if self._history_match is None:
            self._history_match = self._history.match(user_input)
        
    def view_previous_command(self, edit):
        self.ensure_history_match()
        self.replace_current_with_history(edit, self._history_match.prev_command())
        
    def view_next_command(self, edit):
        self.ensure_history_match()
        self.replace_current_with_history(edit, self._history_match.next_command())

    def replace_current_with_history(self, edit, cmd):
        if not cmd:
            return #don't replace if no match
        user_region = sublime.Region(self._output_end, self._view.size())
        self._view.erase(edit, user_region)
        self._view.insert(edit, user_region.begin(), cmd)


class OpenReplCommand(sublime_plugin.WindowCommand):
    def run(self, encoding, type, syntax=None, *args, **kwds):
        try:
            window = self.window
            r = repl.Repl.subclass(type)(encoding, *args, **kwds)
            view = window.new_file()
            rv = ReplView(view, r, syntax)
            repl_views[r.id] = rv
            view.set_scratch(True)
            view.set_name("*REPL* [%s]" % (r.name(),))
        except Exception, e:
            sublime.error_message(str(e))    

class ReplEnterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        v.run_command("insert", {"characters": "\n"})
        if v.sel()[0].begin() != v.size():
            return
        rv = repl_view(v)
        command = rv.user_input()
        rv.adjust_end()
        rv.push_history(command)
        rv.repl.write(command)

class ReplViewPreviousCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        repl_view(self.view).view_previous_command(edit)

class ReplViewNextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        repl_view(self.view).view_next_command(edit)

class SublimeReplListener(sublime_plugin.EventListener):        
    def on_close(self, view):
        rv = repl_view(view)
        if not rv:
            return
        rv.repl.close()