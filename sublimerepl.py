# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.
from __future__ import absolute_import, unicode_literals, print_function, division

import re
import os
import sys
import os.path
import threading
import traceback
from datetime import datetime

import sublime
import sublime_plugin

try:
    import queue
    from . import sublimerepl_build_system_hack
    from . import repls
    from .repllibs import PyDbLite
    unicode_type = str
except ImportError:
    import sublimerepl_build_system_hack
    import repls
    from repllibs import PyDbLite
    import Queue as queue
    unicode_type = unicode

PLATFORM = sublime.platform().lower()
SETTINGS_FILE = 'SublimeREPL.sublime-settings'


class ReplInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, pos, text):
        self.view.insert(edit, int(pos), text)


class ReplEraseTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, start, end):
        self.view.erase(edit, sublime.Region(int(start), int(end)))


class Event:
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def handlers_count(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = handlers_count


class ReplReader(threading.Thread):
    def __init__(self, repl):
        super(ReplReader, self).__init__()
        self.repl = repl
        self.daemon = True
        self.queue = queue.Queue()

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
        self._cur = len(commands)  # no '-1' on purpose

    def current_command(self):
        if not self._commands:
            return ""
        return self._commands[self._cur]

    def prev_command(self):
        self._cur = max(0, self._cur - 1)
        return self.current_command()

    def next_command(self):
        self._cur = min(len(self._commands) - 1, self._cur + 1)
        return self.current_command()


class History(object):
    def __init__(self):
        self._last = None

    def push(self, command):
        cmd = command.rstrip()
        if not cmd or cmd == self._last:
            return
        self.append(cmd)
        self._last = cmd

    def append(self, cmd):
        raise NotImplementedError()

    def match(self, command_prefix):
        raise NotImplementedError()


class MemHistory(History):
    def __init__(self):
        super(MemHistory, self).__init__()
        self._stack = []

    def append(self, cmd):
        self._stack.append(cmd)

    def match(self, command_prefix):
        matching_commands = []
        for cmd in self._stack:
            if cmd.startswith(command_prefix):
                matching_commands.append(cmd)
        return HistoryMatchList(command_prefix, matching_commands)


class PersistentHistory(MemHistory):
    def __init__(self, ext):
        super(PersistentHistory, self).__init__()

    def __init__(self, external_id):
        super(PersistentHistory, self).__init__()
        path = os.path.join(sublime.packages_path(), "User", ".SublimeREPLHistory")
        if not os.path.isdir(path):
            os.makedirs(path)
        filepath = os.path.join(path, external_id + ".db")
        self._db = PyDbLite.Base(filepath)
        self._external_id = external_id
        self._db.create("external_id", "command", "ts", mode="open")

    def append(self, cmd):
        self._db.insert(external_id=self._external_id, command=cmd, ts=datetime.now())
        self._db.commit()

    def match(self, command_prefix):
        retults = [cmd for cmd in self._db if cmd["command"].startswith(command_prefix)]
        return HistoryMatchList(command_prefix, [x["command"] for x in retults])


class ReplView(object):
    def __init__(self, view, repl, syntax):
        self.repl = repl
        self._view = view
        self._window = view.window()

        self.closed = Event()

        if syntax:
            view.set_syntax_file(syntax)
        self._output_end = view.size()

        self._repl_reader = ReplReader(repl)
        self._repl_reader.start()

        settings = sublime.load_settings(SETTINGS_FILE)

        view.settings().set("repl_external_id", repl.external_id)
        view.settings().set("repl_id", repl.id)
        view.settings().set("repl", True)

        rv_settings = settings.get("repl_view_settings", {})
        for setting, value in list(rv_settings.items()):
            view.settings().set(setting, value)

        view.settings().set("history_arrows", settings.get("history_arrows", True))

        # for hysterical rasins ;)
        persistent_history_enabled = settings.get("persistent_history_enabled") or settings.get("presistent_history_enabled")
        if self.external_id and persistent_history_enabled:
            self._history = PersistentHistory(self.external_id)
        else:
            self._history = MemHistory()
        self._history_match = None

        self._filter_color_codes = settings.get("filter_ascii_color_codes")

        # TODO: port, because it's failing
        # optionally move view to a different group
        # find current position of this replview
        # (group, index) = self._window.get_view_index(view

        # get the view that was focussed before the repl was opened.
        # we'll have to focus this one briefly to make sure it's in the
        # foreground again after moving the replview away
        # oldview = self._window.views_in_group(group)[max(0, index - 1)]

        # target = settings.get("open_repl_in_group")

        # either the target group is specified by index
        #if isinstance(target, int):
        #    if 0 <= target < self._window.num_groups() and target != group:
        #        self._window.set_view_index(view, target, len(self._window.views_in_group(target)))
        #        self._window.focus_view(oldview)
        #        self._window.focus_view(view)
        ## or, if simply set to true, move it to the next group from the currently active one
        #elif target and group + 1 < self._window.num_groups():
        #    self._window.set_view_index(view, group + 1, len(self._window.views_in_group(group + 1)))
        #    self._window.focus_view(oldview)
        #    self._window.focus_view(view)

        # begin refreshing attached view
        self.update_view_loop()

    @property
    def external_id(self):
        return self.repl.external_id

    def on_backspace(self):
        if self.delta < 0:
            self._view.run_command("left_delete")

    def on_ctrl_backspace(self):
        if self.delta < 0:
            self._view.run_command("delete_word", {"forward": False, "sub_words": True})

    def on_super_backspace(self):
        if self.delta < 0:
            for i in range(abs(self.delta)):
                self._view.run_command("left_delete")  # Hack to delete to BOL

    def on_left(self):
        if self.delta != 0:
            self._window.run_command("move", {"by": "characters", "forward": False, "extend": False})

    def on_shift_left(self):
        if self.delta != 0:
            self._window.run_command("move", {"by": "characters", "forward": False, "extend": True})

    def on_home(self):
        if self.delta > 0:
            self._window.run_command("move_to", {"to": "bol", "extend": False})
        else:
            for i in range(abs(self.delta)):
                self._window.run_command("move", {"by": "characters", "forward": False, "extend": False})

    def on_shift_home(self):
        if self.delta > 0:
            self._window.run_command("move_to", {"to": "bol", "extend": True})
        else:
            for i in range(abs(self.delta)):
                self._window.run_command("move", {"by": "characters", "forward": False, "extend": True})

    def on_selection_modified(self):
        self._view.set_read_only(self.delta > 0)

    def on_close(self):
        self.repl.close()
        self.closed(self.repl.id)

    def clear(self, edit):
        self.escape(edit)
        self._view.erase(edit, self.output_region)
        self._output_end = self._view.sel()[0].begin()

    def escape(self, edit):
        self._view.set_read_only(False)
        self._view.erase(edit, self.input_region)
        self._view.show(self.input_region)

    def enter(self):
        v = self._view
        if v.sel()[0].begin() != v.size():
            v.sel().clear()
            v.sel().add(sublime.Region(v.size()))

        self.push_history(self.user_input)  # don't include cmd_postfix in history
        v.run_command("insert", {"characters": self.repl.cmd_postfix})
        command = self.user_input
        self.adjust_end()
        self.repl.write(command)

    def previous_command(self, edit):
        self._view.set_read_only(False)
        self.ensure_history_match()
        self.replace_current_input(edit, self._history_match.prev_command())
        self._view.show(self.input_region)

    def next_command(self, edit):
        self._view.set_read_only(False)
        self.ensure_history_match()
        self.replace_current_input(edit, self._history_match.next_command())
        self._view.show(self.input_region)

    def update_view(self, view):
        """If projects were switched, a view could be a new instance"""
        if self._view is not view:
            self._view = view

    def adjust_end(self):
        if self.repl.suppress_echo:
            v = self._view
            vsize = v.size()
            self._output_end = min(vsize, self._output_end)
            v.run_command("repl_erase_text", {"start": self._output_end, "end": vsize})
        else:
            self._output_end = self._view.size()

    def write(self, unistr):
        """Writes output from Repl into this view."""
        # remove color codes
        if self._filter_color_codes:
            unistr = re.sub(r'\033\[\d*(;\d*)?\w', '', unistr)
            unistr = re.sub(r'.\x08', '', unistr)

        # string is assumed to be already correctly encoded
        self._view.run_command("repl_insert_text", {"pos": self._output_end, "text": unistr})
        self._output_end += len(unistr)
        self._view.show(self.input_region)

    def append_input_text(self, text, edit=None):
        e = edit
        if e:
            self._view.insert(e, self._view.size(), text)
        else:
            self._view.run_command("repl_insert_text", {"pos": self._view.size(), "text": text})

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
        except queue.Empty:
            return data, True

    def update_view_loop(self):
        (data, is_still_working) = self.new_output()
        if data:
            self.write(data)
        if is_still_working:
            sublime.set_timeout(self.update_view_loop, 100)
        else:
            self.write("\n***Repl Killed***\n""" if self.repl._killed else "\n***Repl Closed***\n""")
            self._view.set_read_only(True)
            if sublime.load_settings(SETTINGS_FILE).get("view_auto_close"):
                window = self._view.window()
                window.focus_view(self._view)
                window.run_command("close")

    def push_history(self, command):
        self._history.push(command)
        self._history_match = None

    def ensure_history_match(self):
        user_input = self.user_input
        if self._history_match is not None:
            if user_input != self._history_match.current_command():
                # user did something! reset
                self._history_match = None
        if self._history_match is None:
            self._history_match = self._history.match(user_input)

    def replace_current_input(self, edit, cmd):
        if cmd:
            self._view.replace(edit, self.input_region, cmd)
            self._view.sel().clear()
            self._view.sel().add(sublime.Region(self._view.size()))

    def run(self, edit, code):
        self.replace_current_input(edit, code)
        self.enter()
        self._view.show(self.input_region)
        self._window.focus_view(self._view)

    @property
    def input_region(self):
        return sublime.Region(self._output_end, self._view.size())

    @property
    def output_region(self):
        return sublime.Region(0, self._output_end - 2)

    @property
    def user_input(self):
        """Returns text entered by the user"""
        return self._view.substr(self.input_region)

    @property
    def delta(self):
        """Return a repl_view and number of characters from current selection
        to then begging of user_input (otherwise known as _output_end)"""
        return self._output_end - self._view.sel()[0].begin()


class ReplManager(object):

    def __init__(self):
        self.repl_views = {}

    def repl_view(self, view):
        repl_id = view.settings().get("repl_id")
        if repl_id not in self.repl_views:
            return None
        rv = self.repl_views[repl_id]
        rv.update_view(view)
        return rv

    def find_repl(self, external_id):
        for rv in list(self.repl_views.values()):
            if rv.external_id == external_id:
                return rv
        return None

    def find_repl_by_syntax(self, syntax):
        for rv in list(self.repl_views.values()):
            print(rv._view.settings().get('syntax'))
            if rv._view.settings().get('syntax') == syntax:
                return rv
        return None

    def open(self, window, encoding, type, syntax=None, view_id=None, **kwds):
        try:
            kwds = ReplManager.translate(window, kwds)
            encoding = ReplManager.translate(window, encoding)
            r = repls.Repl.subclass(type)(encoding, **kwds)
            found = None
            for view in window.views():
                if view.id() == view_id:
                    found = view
                    break
            view = found or window.new_file()

            rv = ReplView(view, r, syntax)
            rv.closed += self._delete_repl
            self.repl_views[r.id] = rv
            view.set_scratch(True)
            view.set_name("*REPL* [%s]" % (r.name(),))
            return rv
        except Exception as e:
            traceback.print_exc()
            sublime.error_message(repr(e))

    def _delete_repl(self, repl_id):
        if repl_id not in self.repl_views:
            return None
        del self.repl_views[repl_id]

    @staticmethod
    def translate(window, obj, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        if isinstance(obj, dict):
            return ReplManager._translate_dict(window, obj, subst)
        if isinstance(obj, unicode_type):  # PY2
            return ReplManager._translate_string(window, obj, subst)
        if isinstance(obj, list):
            return ReplManager._translate_list(window, obj, subst)
        return obj

    @staticmethod
    def _subst_for_translate(window):
        """ Return all available substitutions"""
        import locale
        res = {
            "packages": sublime.packages_path(),
            "installed_packages": sublime.installed_packages_path()
        }
        res["editor"] = "subl -w"
        res["win_cmd_encoding"] = "utf8"
        if sublime.platform() == "windows":
            res["win_cmd_encoding"] = locale.getdefaultlocale()[1]
            res["editor"] = '"%s"' % (sys.executable,)
        av = window.active_view()
        if av is None:
            return res
        filename = av.file_name()
        if not filename:
            return res
        filename = os.path.abspath(filename)
        res["file"] = filename
        res["file_path"] = os.path.dirname(filename)
        res["file_basename"] = os.path.basename(filename)
        if window.folders():
            res["folder"] = window.folders()[0]
        else:
            res["folder"] = res["file_path"]

        if sublime.load_settings(SETTINGS_FILE).get("use_build_system_hack", False):
            project_settings = sublimerepl_build_system_hack.get_project_settings(window)
            res.update(project_settings)

        return res

    @staticmethod
    def _translate_string(window, string, subst=None):
        from string import Template
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        return Template(string).safe_substitute(**subst)

    @staticmethod
    def _translate_list(window, list, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        return [ReplManager.translate(window, x, subst) for x in list]

    @staticmethod
    def _translate_dict(window, dictionary, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        if PLATFORM in dictionary:
            return ReplManager.translate(window, dictionary[PLATFORM], subst)
        for k, v in list(dictionary.items()):
            dictionary[k] = ReplManager.translate(window, v, subst)
        return dictionary

manager = ReplManager()

# Window Commands #########################################


# Opens a new REPL
class ReplOpenCommand(sublime_plugin.WindowCommand):
    def run(self, encoding, type, syntax=None, view_id=None, **kwds):
        manager.open(self.window, encoding, type, syntax, view_id, **kwds)


# View Commands ###########################################

# Send selection/line to REPL
class ReplSendNewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        ## TODO: see text_transfer.py!
        syntax = self.view.settings().get('syntax')
        rv = manager.find_repl_by_syntax(syntax)
        if not rv:
            return

        lines = []
        for region in self.view.sel():
            if region.empty():
                line = self.view.substr(self.view.line(region))
            else:
                line = self.view.substr(region)
            lines.append(line)

        cmd = '\n'.join(lines)
        print(cmd)
        rv.run(edit, cmd)

# REPL Comands ############################################


# Submits the Command to the REPL
class ReplEnterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.enter()


class ReplClearCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.clear(edit)


# Resets Repl Command Line
class ReplEscapeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.escape(edit)


def repl_view_delta(sublime_view):
    """Return a repl_view and number of characters from current selection
    to then beggingin of user_input (otherwise known as _output_end)"""
    rv = repl_view(sublime_view)
    if not rv:
        return None, -1
    delta = rv._output_end - sublime_view.sel()[0].begin()
    return rv, delta


class ReplBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_backspace()


class ReplCtrlBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_ctrl_backspace()


class ReplSuperBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_super_backspace()


class ReplLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_left()


class ReplShiftLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_shift_left()


class ReplHomeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_home()


class ReplShiftHomeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_shift_home()


class ReplViewPreviousCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.previous_command(edit)


class ReplViewNextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.next_command(edit)


class ReplKillCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.repl.kill()


class SublimeReplListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        rv = manager.repl_view(view)
        if rv:
            rv.on_selection_modified()

    def on_close(self, view):
        rv = manager.repl_view(view)
        if rv:
            rv.on_close()


class SubprocessReplSendSignal(sublime_plugin.TextCommand):
    def run(self, edit, signal=None):
        rv = manager.repl_view(self.view)
        subrepl = rv.repl
        signals = subrepl.available_signals()
        sorted_names = sorted(signals.keys())
        if signal in signals:
            #signal given by name
            self.safe_send_signal(subrepl, signals[signal])
            return
        if signal in list(signals.values()):
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
        except Exception as e:
            sublime.error_message(str(e))

    def is_visible(self):
        rv = manager.repl_view(self.view)
        return bool(rv) and hasattr(rv.repl, "send_signal")

    def is_enabled(self):
        return self.is_visible()

    def description(self):
        return "Send SIGNAL"
