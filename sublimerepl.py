
import threading
import Queue

class Reader(threading.Thread):
	def __init__(self, in_stream, queue):
		super(Reader, self).__init__()
		self.in_stream = in_stream
		self.queue = queue
		self.daemon = True

	def run(self):
		while True:
			data = self.in_stream.read()
			self.queue.put(data)
			if not data:
				break
		print ("Reader exiting")


class Writer(threading.Thread):
	def __init__(self, queue):
		super(Writer, self).__init__()
		self.daemon = True
		self.queue = queue

	def run(self):
		import time
		while True:
			try:
				data = self.queue.get_nowait()
				if not data:
					break
				self.write(data)
			except Queue.Empty, e:
				time.sleep(0.1)

	def write(self, data):
		import sys
		sys.stdout.write(data)
		sys.stdout.flush()


class SubprocessREPL(object):
	def __init__(self, cmd="cmd"):
		import subprocess, os
		startupinfo = None
		if os.name == 'nt':
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		self.popen = subprocess.Popen(cmd, startupinfo=startupinfo, bufsize=256, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

	def read(self):
		data = self.popen.stdout.read(1)
		if not data:
			return None
		return data

	def write(self, data):
		self.popen.stdin.write(data)
		self.popen.stdin.flush()

	def close(self):
		self.popen.kill()

	def working(self):
		return self.popen.poll() is None

		
class SublimeWriter(object):
	def __init__(self, queue, view):
		self.queue = queue
		self.view = view
		self.adjust_end()

	def adjust_end(self):
		self.end = self.view.size()

	def entered_text(self):
		return self.view.substr(sublime.Region(self.end, self.view.size()))

	def start(self):
		sublime.set_timeout(self.write, 100)

	def int_write(self, data):
		view = self.view
		edit = view.begin_edit()
		view.insert(edit, self.end, data.decode("cp1250"))
		self.end += len(data)
		view.end_edit(edit)

		if view.sel()[0].end() == view.size():
			view.show(view.line(view.size()).begin())

	def write(self):
		(data, leave) = self.data()
		if data:
			self.int_write(data)
		if leave:
			self.int_write("***EXIT***")
			return
		self.start()

	def data(self):
		data = ""
		try:
			while True:
				packet = self.queue.get_nowait()
				if packet is None:
					return data, True
				data += packet
		except Queue.Empty, e:
			return data, False


import sublime, sublime_plugin

class SublimeREPL(object):

	def __init__(self, window, cmd="python -i", name="repl"):
		self.queue = Queue.Queue()
		self.repl = SubprocessREPL(cmd)
		self.reader = Reader(self.repl, self.queue)
		
		self.view = window.new_file()
		self.view.set_scratch(True)
		self.view.set_name(name)

		self.writer = SublimeWriter(self.queue, self.view)

		self.reader.start()
		self.writer.start()

	def send(self):
		data = self.writer.entered_text()
		self.writer.adjust_end()
		self.repl.write(data.encode("cp1250"))

	def close(self):
		self.repl.close()



repls = {}

class SublimeREPLListener(sublime_plugin.EventListener):

	def repl(self, view):
		if not repls.has_key(view.id()):
			return 
		return repls[view.id()]
		
	def on_close(self, view):
		repl = self.repl(view)
		if not repl:
			return
		print "closing"
		repl.close()

	def on_modified(self, view):
		repl = self.repl(view)
		if not repl:
			return
		view = repl.view
		sel = view.sel()[0]
		if sel.end() != sel.begin() or sel.end() != view.size():
			return
		last = view.substr(sublime.Region(view.size() - 1, view.size()))
		if last != "\n":
			return
		repl.send()


class OpenReplCommand(sublime_plugin.WindowCommand):
	def run(self, cmd):
		window = self.window
		r = SublimeREPL(window, cmd)
		repls[r.view.id()] = r

import sys
if __name__ == "__main__":
	q = Queue.Queue()
	sr = SubprocessREPL()#"python -i ")
	r = Reader(sr, q)
	w = Writer(q)
	r.start()
	w.start()
	while True:
		if not sr.working():
			break
		d = raw_input()
		if not d:
			if not sr.working():
				break
			sr.write("\n")
			continue
		sr.write(d + "\n")
	raw_input("All exit")
