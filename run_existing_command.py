import os
import json
import codecs
import sublime
import sublime_plugin

SUBLIMEREPL_DIR = None
SUBLIMEREPL_USER_DIR = None

def plugin_loaded():
    global SUBLIMEREPL_DIR
    global SUBLIMEREPL_USER_DIR
    SUBLIMEREPL_DIR = "Packages/SublimeREPL"
    SUBLIMEREPL_USER_DIR = os.path.join(sublime.packages_path(), "User", "SublimeREPL")

# yes, CommandCommmand :) 
class RunExistingWindowCommandCommand(sublime_plugin.WindowCommand):
    def run(self, id, file):
        """Find and run existing command with id in specified file. 
        SUBLIMEREPL_USER_DIR is consulted first, and then SUBLIMEREPL_DIR""" 
        for prefix in (SUBLIMEREPL_USER_DIR, SUBLIMEREPL_DIR):
            path = os.path.join(prefix, file)
            json_cmd = self._find_cmd(id, path)
            if json_cmd:
                break
        if not json_cmd:
            return
        args = json_cmd["args"] if "args" in json_cmd else None
        self.window.run_command(json_cmd["command"], args)
    
    def _find_cmd(self, id, file):
        return self._find_cmd_in_file(id, file)
                
    def _find_cmd_in_file(self, id, file):
        try:
            f = sublime.load_resource(file)
            data = json.loads(f)
            return self._find_cmd_in_json(id, data)
        except (IOError, ValueError):
            return None

    def _find_cmd_in_json(self, id, json_object):
        if isinstance(json_object, list):
            for elem in json_object:
                cmd = self._find_cmd_in_json(id, elem)
                if cmd:
                    return cmd
        elif isinstance(json_object, dict):
            if "id" in json_object and json_object["id"] == id:
                return json_object
            elif "children" in json_object:
                return self._find_cmd_in_json(id, json_object["children"])
        return None