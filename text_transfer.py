from __future__ import absolute_import, unicode_literals, print_function, division

import re
import sublime_plugin
import sublime
from collections import defaultdict
import tempfile
import binascii

try:
    from .sublimerepl import manager, SETTINGS_FILE
except (ImportError, ValueError):
    from sublimerepl import manager, SETTINGS_FILE


def default_sender(repl, text, view=None, repl_view=None):
    if repl.apiv2:
        repl.write(text, location=repl_view.view.size() - len(text))
    else:
        repl.write(text)

    if view is None or not sublime.load_settings(SETTINGS_FILE).get('focus_view_on_transfer'):
        return
    active_window = sublime.active_window()
    active_view = active_window.active_view()
    target_view = repl_view.view
    if target_view == active_view:
        return  #
    active_group = sublime.active_window().active_group()
    if target_view in active_window.views_in_group(active_group):
        return  # same group, dont switch
    active_window.focus_view(target_view)
    active_window.focus_view(view)


"""Senders is a dict of functions used to transfer text to repl as a repl
   specific load_file action"""
SENDERS = defaultdict(lambda: default_sender)


def sender(external_id,):
    def wrap(func):
        SENDERS[external_id] = func
    return wrap


@sender("coffee")
def coffee(repl, text, view=None, repl_view=None):
    """
        use CoffeeScript multiline hack
        http://coffeescript.org/documentation/docs/repl.html
    """
    default_sender(repl, text.replace("\n", u'\uFF00') + "\n", view, repl_view)

@sender("python")
def python_sender(repl, text, view=None, repl_view=None):
    text_wo_encoding = re.sub(
        pattern=r"#.*coding[:=]\s*([-\w.]+)",
        repl="# <SublimeREPL: encoding comment removed>",
        string=text,
        count=1)
    code = binascii.hexlify(text_wo_encoding.encode("utf-8"))
    execute = ''.join([
        'from binascii import unhexlify as __un; exec(compile(__un("',
        str(code.decode('ascii')),
        '").decode("utf-8"), "<string>", "exec"))\n'
    ])
    return default_sender(repl, execute, view, repl_view)


@sender("ruby")
def ruby_sender(repl, text, view=None, repl_view=None):
    code = binascii.b2a_base64(text.encode("utf-8"))
    payload = "begin require 'base64'; eval(Base64.decode64('%s'), binding=TOPLEVEL_BINDING) end\n" % (code.decode("ascii"),)
    return default_sender(repl, payload, view, repl_view)


# custom clojure sender that makes sure that all selections are
# evaluated in the namespace declared by the file they are in
@sender("clojure")
def clojure_sender(repl, text, view, repl_view=None):
    # call (load-string) instead of just writing the string so
    # that syntax errors are caught and thrown back immediately.
    # also, escape backslashes and double-quotes
    text = '(load-string "' + text.strip().replace('\\', r'\\').replace('"', r'\"') + '")'

    # find the first non-commented statement from the start of the file
    namespacedecl = view.find(r"^[^;]*?\(", 0)

    # if it's a namespace declaration, go search for the namespace name
    if namespacedecl and view.scope_name(namespacedecl.end()-1).startswith("source.clojure meta.function.namespace.clojure"):
        namespacedecl = view.extract_scope(namespacedecl.end()-1)

        # we're looking for the first symbol within the declaration that
        # looks like a namespace and isn't metadata, a comment, etc.
        pos = namespacedecl.begin() + 3
        while pos < namespacedecl.end():
            # see http://clojure.org/reader for a description of valid
            # namespace names. the inital } or whitespace make sure we're
            # not matching on keywords etc.
            namespace = view.find(r"[\}\s][A-Za-z\_!\?\*\+\-][\w!\?\*\+\-:]*(\.[\w!\?\*\+\-:]+)*", pos)

            if not namespace:
                # couldn't find the namespace name within the declaration. suspicious.
                break
            elif view.scope_name(namespace.begin() + 1).startswith("source.clojure meta.function.namespace.clojure entity.name.namespace.clojure"):
                # looks alright, we've got our namespace!
                # switch to namespace before executing command

                # we could do this explicitly by calling (ns), (in-ns) etc:
                # text = "(ns " + view.substr(namespace)[1:] + ") " + text
                # but this would not only result in an extra return value
                # printed to the user, the repl would also remain in that
                # namespace after execution, so instead we do the same thing
                # that swank-clojure does:
                text = "(binding [*ns* (or (find-ns '" + view.substr(namespace)[1:] + ") (find-ns 'user))] " + text + ')'
                # i.e. we temporarily switch to the namespace if it has already
                # been created, otherwise we execute it in 'user. the most
                # elegant option for this would probably be:
                # text = "(binding [*ns* (create-ns '" + view.substr(namespace)[1:] + ")] " + text + ')'
                # but this can lead to problems because of newly created
                # namespaces not automatically referring to clojure.core
                # (see https://groups.google.com/forum/?fromgroups=#!topic/clojure/Th-Bqq68hfo)
                break
            else:
                # false alarm (metadata or a comment), keep looking
                pos = namespace.end()
    return default_sender(repl, text + repl.cmd_postfix, view, repl_view)

class ReplViewWrite(sublime_plugin.TextCommand):
    def run(self, edit, external_id, text):
        for rv in manager.find_repl(external_id):
            rv.append_input_text(text)
            break  # send to first repl found
        else:
            sublime.error_message("Cannot find REPL for '{0}'".format(external_id))


class ReplSend(sublime_plugin.TextCommand):
    def run(self, edit, external_id, text, with_auto_postfix=True):
        for rv in manager.find_repl(external_id):
            if with_auto_postfix:
                text += rv.repl.cmd_postfix
            if sublime.load_settings(SETTINGS_FILE).get('show_transferred_text'):
                rv.append_input_text(text)
                rv.adjust_end()
            SENDERS[external_id](rv.repl, text, self.view, rv)
            break
        else:
            sublime.error_message("Cannot find REPL for '{}'".format(external_id))


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
        self.view.window().run_command(cmd, {"external_id": self.repl_external_id(), "text": text})

    def repl_external_id(self):
        return self.view.scope_name(0).split(" ")[0].split(".", 1)[1]

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
