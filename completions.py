import sublime
import sublime_plugin

import json
import socket


class SublimeREPLCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.settings().get("repl"):
            return True
        from sublimerepl import manager
        rv = manager.repl_view(view)
        whole_prefix = view.substr(sublime.Region(rv._output_end, locations[0]))
        print view, prefix, locations, whole_prefix
        flags = sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("localhost", 9999))
        try:
            ## TODO: split
            text = whole_prefix
            for ch in [' ', '(', ',']:
                text_parts = text.rsplit(ch, 1)
                text = text_parts.pop()
            s.sendall(json.dumps({"line": whole_prefix, "text": text, "cursor_pos": len(whole_prefix)}) + "\n")
            res = json.loads(s.recv(65535))
        finally:
            s.close()

        comp = [(x,x) for x in res[1]]
        return (comp, flags)
