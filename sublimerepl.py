# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net) 
# All rights reserved. 
# See LICENSE.txt for details.

import threading
import Queue
import sublime
import sublime_plugin
import repl

repl_views = {}

PLATFORM = sublime.platform().lower()

def repl_view(view):
    id = view.settings().get("repl_id")
    if not repl_views.has_key(id):
        return None
    rv = repl_views[id]
    rv.update_view(view)
    return rv

def find_repl(external_id):
    for rv in repl_views.values():
        if rv.external_id == external_id:
            return rv
    return None

def _delete_repl(view):
    id = view.settings().get("repl_id")
    if not repl_views.has_key(id):
        return None
    del repl_views[id]


def subst_for_translate(window):
    """ Return all available substitutions"""
    import os.path
    res = {
        "packages": sublime.packages_path(),
        "installed_packages" : sublime.installed_packages_path()
        }
    av = window.active_view()
    if av is None:
        return res
    filename = av.file_name()
    if not filename:
        return res
    filename = os.path.abspath(filename)
    res["file"] = filename
    res["file_path"] = os.path.dirname(filename)
    return res


def translate_string(window, string, subst=None):
    #$file, $file_path, $packages
    from string import Template
    if subst is None:
        subst = subst_for_translate(window)
    return Template(string).safe_substitute(**subst)

def translate_list(window, list, subst=None):
    if subst is None:
        subst = subst_for_translate(window)
    return [translate(window, x, subst) for x in list]

def translate_dict(window, dictionary, subst=None):
    if subst is None:
        subst = subst_for_translate(window)
    if PLATFORM in dictionary:
        return translate(window, dictionary[PLATFORM], subst)
    for k, v in dictionary.items():
        dictionary[k] = translate(window, v, subst)
    return dictionary

def translate(window, obj, subst=None):
    if subst is None:
        subst = subst_for_translate(window)
    if isinstance(obj, dict):
        return translate_dict(window, obj, subst)
    if isinstance(obj, basestring):
        return translate_string(window, obj, subst)
    if isinstance(obj, list):
        return translate_list(window, obj, subst)
    return obj

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
        
        self._repl_reader = ReplReader(repl)
        self._repl_reader.start()

        self._history = History()
        self._history_match = None
        
        # begin refreshing attached view
        self.update_view_loop()

    @property
    def external_id(self):
        return self.repl.external_id

    def update_view(self, view):
        """If projects were switched, a view could be a new instance"""
        if self._view is not view:
            self._view = view

    def user_input(self):
        """Returns text entered by the user"""
        region = sublime.Region(self._output_end, self._view.size())
        return self._view.substr(region)

    def adjust_end(self):
        if self.repl.suppress_echo:
            v = self._view
            edit = v.begin_edit()
            v.erase(edit, sublime.Region(self._output_end, v.size()))
            v.end_edit(edit)
        else:
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

    def append_input_text(self, text, edit=None):
        e = edit
        if not edit:
            e = self._view.begin_edit()
        self._view.insert(e, self._view.size(), text)
        if not edit:
            self._view.end_edit(e)

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


class ReplOpenCommand(sublime_plugin.WindowCommand):
    def run(self, encoding, type, syntax=None, **kwds):
        try:
            window = self.window
            kwds = translate(window, kwds)
            r = repl.Repl.subclass(type)(encoding, **kwds)
            view = window.new_file()
            rv = ReplView(view, r, syntax)
            repl_views[r.id] = rv
            view.set_scratch(True)
            view.set_name("*REPL* [%s]" % (r.name(),))
            return rv
        except Exception, e:
            sublime.error_message(str(e))    


class ReplEnterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        if v.sel()[0].begin() != v.size():
            v.run_command("insert", {"characters": "\n"})
            return
        rv = repl_view(v)
        rv.push_history(rv.user_input()) # don't include cmd_postfix in history
        v.run_command("insert", {"characters": rv.repl.cmd_postfix})
        command = rv.user_input()
        rv.adjust_end()
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
        _delete_repl(view)


class SubprocessReplSendSignal(sublime_plugin.TextCommand):
    def run(self, edit, signal=None):
        rv = repl_view(self.view)
        subrepl = rv.repl
        signals = subrepl.available_signals()
        sorted_names = sorted(signals.keys())              
        if signals.has_key(signal):
            #signal given by name
            self.safe_send_signal(subrepl, signals[signal])
            return
        if signal in signals.values():
            #signal given by code (correct one!)
            self.safe_send_signal(subrepl, signal)
            return
        # no or incorrect signal given
        def signal_selected(num):
            if num == -1:
                return
            signame = sorted_names[num]
            sigcode = signals[signame]
            self.safe_send_signal(subrepl, sigcode)
        self.view.window().show_quick_panel(sorted_names, signal_selected)
                
    def safe_send_signal(self, subrepl, sigcode):
        try:
            subrepl.send_signal(sigcode)
        except Exception, e:
            sublime.error_message(str(e))

    def is_visible(self):
        rv = repl_view(self.view)
        return rv and hasattr(rv.repl, "send_signal")

    def is_enabled(self):
        return self.is_visible()

    def description(self):
        return "Send SIGNAL"



