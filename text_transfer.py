from sublimerepl import find_repl
import sublime_plugin
import sublime
import paragraph

class ReplViewWrite(sublime_plugin.WindowCommand):
    def run(self, external_id, text):
        rv = find_repl(external_id)
        if not rv:
            return
        rv.append_input_text(text)


class ReplSend(sublime_plugin.WindowCommand):
    def run(self, external_id, text, with_auto_postfix=True):
        rv = find_repl(external_id)
        if not rv:
            return
        cmd = text
        if with_auto_postfix:
            cmd += rv.repl.cmd_postfix
        rv.repl.write(cmd)


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
        elif scope == "paragraph":
            text = self.current_paragraph() + "\n"
            print text
        cmd = "repl_" + action
        self.view.window().run_command(cmd, {"external_id": self.repl_external_id(), "text": text})

    def repl_external_id(self):
        return self.view.scope_name(0).split(" ")[0].split(".")[1]

    def selected_text(self):
        v = self.view
        parts = [v.substr(region) for region in v.sel()]
        return "".join(parts)

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

    def current_paragraph(self):
        v = self.view
        for s in v.sel():
            return v.substr(paragraph.expand_to_paragraph(v, s.begin()))


