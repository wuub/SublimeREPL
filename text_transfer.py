from sublimerepl import find_repl
import sublime_plugin

class ReplWriteTo(sublime_plugin.TextCommand):
    def run(self, edit, external_id, text):
        rv = find_repl(external_id)
        if not rv:
            return 
        rv.append_input_text(edit, text)