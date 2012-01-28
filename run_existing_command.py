import json
import codecs
import sublime
import sublime_plugin

# yes, CommandCommmand :) 
class RunExistingWindowCommandCommand(sublime_plugin.WindowCommand):
	def run(self, cmd_id, filepath):
		json_cmd = self._find_cmd(cmd_id, filepath)
		if not json_cmd:
			return
		cmd = json_cmd["command"]
		args = json_cmd["args"] if "args" in json_cmd else None
		self.window.run_command(cmd, args)
	
	def _find_cmd(self, cmd_id, filepath):
		return self._find_cmd_in_file(cmd_id, filepath)
				
	def _find_cmd_in_file(self, cmd_id, filepath):

		try:
			with codecs.open(filepath, "r", "utf-8") as f:
				lines = [line.split("//")[0] for line in f.readlines()]
				data = json.loads("\n".join(lines))
			return self._find_cmd_in_json(cmd_id, data)
		except (IOError, ValueError), e:
			print sublime.error_message(str(e))

	def _find_cmd_in_json(self, cmd_id, json_object):
		if isinstance(json_object, list):
			for elem in json_object:
				cmd = self._find_cmd_in_json(cmd_id, elem)
				if cmd:
					return cmd
		elif isinstance(json_object, dict):
			if "id" in json_object and json_object["id"] == cmd_id:
				return json_object
			elif "children" in json_object:
				return self._find_cmd_in_json(cmd_id, json_object["children"])
		return None
		


#sublime.active_window().run_command("run_existing_window_command", {"cmd_id": "hello"})