import os
import json
import codecs
import sublime
import sublime_plugin

SUBLIMEREPL_DIR = os.getcwdu()

# yes, CommandCommmand :) 
class RunExistingWindowCommandCommand(sublime_plugin.WindowCommand):
	def run(self, id, file):
		path = os.path.join(SUBLIMEREPL_DIR, file)
		json_cmd = self._find_cmd(id, path)
		if not json_cmd:
			return
		args = json_cmd["args"] if "args" in json_cmd else None
		self.window.run_command(json_cmd["command"], args)
	
	def _find_cmd(self, id, file):
		return self._find_cmd_in_file(id, file)
				
	def _find_cmd_in_file(self, id, file):

		try:
			with codecs.open(file, "r", "utf-8") as f:
				lines = [line.split("//")[0] for line in f.readlines()]
				data = json.loads("\n".join(lines))
			return self._find_cmd_in_json(id, data)
		except (IOError, ValueError), e:
			print sublime.error_message(str(e))

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
		


#sublime.active_window().run_command("run_existing_window_command", {"id": "hello"})