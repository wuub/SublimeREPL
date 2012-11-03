import sublime
import sublime_plugin


class SublimeREPLCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.settings().get("repl"):
            return True

        from sublimerepl import manager
        rv = manager.repl_view(view)
        if not rv:
            return []

        repl = rv.repl
        if not repl.autocomplete_available():
            return []

        whole_prefix = view.substr(sublime.Region(rv._output_end, locations[0]))

        completions = repl.autocomplete_completions(prefix=prefix, whole_prefix=whole_prefix, locations=locations)
        return completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
