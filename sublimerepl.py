import threading
import Queue
import sublime


class Repl(object):
    """Class that represents a process that is being executed.
       For example this can be python, bash or a telnet session"""

    def __init__(self, encoding):
        from uuid import uuid4
        from codecs import getincrementaldecoder, getencoder
        self.id = uuid4().hex
        self.decoder = getincrementaldecoder(encoding)()
        self.encoder = getencoder(encoding)

    def is_alive(self):
        """ Returns true if the undelying process is stil working"""
        raise NotImplementedError
    
    def write_bytes(self, bytes):
        raise NotImplementedError        

    def read_bytes(self):
        """Reads at lest one byte of Repl output. Returns None if output died.
           Can block!!!"""
        raise NotImplementedError

    def close(self):
        """Closes underlying repl"""
        raise NotImplementedError

    def write(self, command):
        """Encodes and evaluates a given command"""
        (bytes, how_many) = self.encoder(command)
        return self.write_bytes(bytes)

    def read(self):
        """Reads at least one decoded char of output"""
        while True:
            bs = self.read_bytes()
            if not bs:
                return None
            output = self.decoder.decode(bs)
            if output:
                return output


class ReplReader(threading.Thread):
    def __init__(self, repl):
        super(ReplReader, self).__init__()
        self.repl = repl
        self.daemon = True
        self.queue = Queue.Queue()

    def run(self):
        r = self.repl
        q = self.queue
        while True:
            result = r.read()
            q.put(result)
            if result is None:
                break
        print("Reader exiting")


class HistoryMatchList(object):
    def __init__(self, command_prefix, commands):
        self._command_prefix = command_prefix
        self._commands = commands
        self._cur = len(commands) # no '-1' on purpose

    def current_command(self):
        if not self._commands:
            return ""
        return self._commands[self._cur]

    def prev_command(self):
        self._cur = max(0, self._cur - 1)
        return self.current_command()

    def next_command(self):
        self._cur = min(len(self._commands) -1, self._cur + 1)
        return self.current_command()


class History(object):
    def __init__(self):
        self._stack = []

    def push(self, command):
        cmd = command.strip()
        if not cmd:
            return
        self._stack.append(cmd)

    def match(self, command_prefix):
        matching_commands = []
        for cmd in self._stack:
            if cmd.startswith(command_prefix):
                matching_commands.append(cmd)
        return HistoryMatchList(command_prefix, matching_commands)

class ReplView(object):
    def __init__(self, view, repl, *args, **kwds):
        view.settings().set("repl_id", repl.id)
        view.settings().set("repl", True)
        self.repl = repl
        # init
        self._view = view
        self._output_end = view.size()
        self._repl_reader = ReplReader(repl)
        self._repl_reader.start()
        self._history = History()
        self._history_match = None
        # begin refreshing attached view
        self.update_view_loop()

    def update_view(self, view):
        """If projects were switched, a view could be a new instance"""
        if self._view is not view:
            self._view = view

    def user_input(self):
        """Returns text entered by the user"""
        region = sublime.Region(self._output_end, self._view.size())
        return self._view.substr(region)

    def adjust_end(self):
        self._output_end = self._view.size()

    def write(self, unistr):
        """Writes output from Repl into this view."""
        # string is assumet to be already correctly encoded
        v = self._view
        edit = v.begin_edit()
        try:
            v.insert(edit, self._output_end, unistr)
            self._output_end += len(unistr)
        finally:
            v.end_edit(edit)
        self.scroll_to_end()

    def scroll_to_end(self):
        v = self._view
        v.show(v.line(v.size()).begin())

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
        except Queue.Empty:
            return data, True

    def update_view_loop(self):
        (data, is_still_working) = self.new_output()
        if data:
            self.write(data)
        if is_still_working:
            sublime.set_timeout(self.update_view_loop, 100)

    def push_history(self, command):
        self._history.push(command)
        self._history_match = None

    def ensure_history_match(self):
        user_input = self.user_input()
        if self._history_match is not None:
            if user_input != self._history_match.current_command():
                # user did something! reset
                self._history_match = None
        if self._history_match is None:
            self._history_match = self._history.match(user_input)
        
    def view_previous_command(self, edit):
        self.ensure_history_match()
        self.replace_current_with_history(edit, self._history_match.prev_command())
        
    def view_next_command(self, edit):
        self.ensure_history_match()
        self.replace_current_with_history(edit, self._history_match.next_command())

    def replace_current_with_history(self, edit, cmd):
        if not cmd:
            return #don't replace if no match
        user_region = sublime.Region(self._output_end, self._view.size())
        self._view.erase(edit, user_region)
        self._view.insert(edit, user_region.begin(), cmd)



class SubprocessRepl(Repl):
    def __init__(self, encoding, cmd, *args, **kwds):
        import subprocess, os
        super(SubprocessRepl, self).__init__(encoding)
        self.popen = subprocess.Popen(
                        cmd, 
                        bufsize=1, 
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE)


    def is_alive(self):
        return self.popen.poll() is None

    def read_bytes(self):
        # this is windows specific problem, that you cannot tell if there 
        # are more bytes ready, so we read
        return self.popen.stdout.read(1)

    def write_bytes(self, bytes):
        si = self.popen.stdin 
        si.write(bytes)
        si.flush()

    def close(self):
        if self.is_alive():
            self.popen.kill()


import sublime_plugin
repls = {}

def repl_view(view):
    id = view.settings().get("repl_id")
    if not repls.has_key(id):
        return None
    rv = repls[id]
    rv.update_view(view)
    return rv


class OpenReplCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        view = window.new_file()
        view.set_scratch(True)
        cmd = ["cmd", "/Q"]
        r = SubprocessRepl("cp852", cmd)
        rv = ReplView(view, r)
        repls[r.id] = rv
        

class ReplEnterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        v = self.view
        v.run_command("insert", {"characters": "\n"})
        if v.sel()[0].begin() != v.size():
            return
        rv = repl_view(v)
        command = rv.user_input()
        rv.adjust_end()
        rv.push_history(command)
        rv.repl.write(command)

class ReplViewPreviousCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        repl_view(self.view).view_previous_command(edit)

class ReplViewNextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        repl_view(self.view).view_next_command(edit)

class SublimeReplListener(sublime_plugin.EventListener):        
    def on_close(self, view):
        rv = repl_view(view)
        if not rv:
            return
        print "closing"
        rv.repl.close()

#     def on_modified(self, view):
#         rv = self.rv(view)
#         if not rv:
#             return
#         sel = view.sel()[0]
#         if sel.end() != sel.begin() or sel.end() != view.size():
#             return
#         last = view.substr(sublime.Region(view.size() - 1, view.size()))
#         if last != "\n":
#             return
#         command = rv.user_input()
#         rv.adjust_end()
#         rv.repl.write(command)


# class Reader(threading.Thread):
#     def __init__(self, in_stream, queue):
#         super(Reader, self).__init__()
#         self.in_stream = in_stream
#         self.queue = queue
#         self.daemon = True

#     def run(self):
#         while True:
#             data = self.in_stream.read()
#             self.queue.put(data)
#             if not data:
#                 break
#         print ("Reader exiting")


# class Writer(threading.Thread):
#     def __init__(self, queue):
#         super(Writer, self).__init__()
#         self.daemon = True
#         self.queue = queue

#     def run(self):
#         import time
#         while True:
#             try:
#                 data = self.queue.get_nowait()
#                 if not data:
#                     break
#                 self.write(data)
#             except Queue.Empty, e:
#                 time.sleep(0.1)

#     def write(self, data):
#         import sys
#         sys.stdout.write(data)
#         sys.stdout.flush()


# class SubprocessRepl(object):
#     def __init__(self, cmd="cmd"):
#         import subprocess, os
#         startupinfo = None
#         if os.name == 'nt':
#             startupinfo = subprocess.STARTUPINFO()
#             startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#         self.popen = subprocess.Popen(cmd, startupinfo=startupinfo, bufsize=256, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

#     def read(self):
#         data = self.popen.stdout.read(1)
#         if not data:
#             return None
#         return data

#     def write(self, data):
#         self.popen.stdin.write(data)
#         self.popen.stdin.flush()

#     def close(self):
#         self.popen.kill()

#     def working(self):
#         return self.popen.poll() is None

        
# class SublimeWriter(object):
#     def __init__(self, queue, view):
#         self.queue = queue
#         self._view = view
#         self.adjust_end()

#     def adjust_end(self):
#         self.end = self._view.size()

#     def entered_text(self):
#         return self._view.substr(sublime.Region(self.end, self._view.size()))

#     def start(self):
#         sublime.set_timeout(self.write, 100)

#     def int_write(self, data):
#         view = self._view
#         edit = view.begin_edit()
#         view.insert(edit, self.end, data.decode("cp1250"))
#         self.end += len(data)
#         view.end_edit(edit)

#         if view.sel()[0].end() == view.size():
#             view.show(view.line(view.size()).begin())

#     def write(self):
#         (data, leave) = self.data()
#         if data:
#             self.int_write(data)
#         if leave:
#             self.int_write("***EXIT***")
#             return
#         self.start()

#     def data(self):
#         data = ""
#         try:
#             while True:
#                 packet = self.queue.get_nowait()
#                 if packet is None:
#                     return data, True
#                 data += packet
#         except Queue.Empty, e:
#             return data, False


# import sublime, sublime_plugin

# class SublimeRepl(object):

#     def __init__(self, window, cmd="python -i", name="repl"):
#         self.queue = Queue.Queue()
#         self.repl = SubprocessRepl(cmd)
#         self.reader = Reader(self.repl, self.queue)
        
#         self._view = window.new_file()
#         self._view.set_scratch(True)
#         self._view.set_name(name)

#         self.writer = SublimeWriter(self.queue, self._view)

#         self.reader.start()
#         self.writer.start()

#     def send(self):
#         data = self.writer.entered_text()
#         self.writer.adjust_end()
#         self.repl.write(data.encode("cp1250"))

#     def close(self):
#         self.repl.close()



# repls = {}

# class SublimeReplListener(sublime_plugin.EventListener):

#     def repl(self, view):
#         if not repls.has_key(view.id()):
#             return 
#         return repls[view.id()]
        
#     def on_close(self, view):
#         repl = self.repl(view)
#         if not repl:
#             return
#         print "closing"
#         repl.close()

#     def on_modified(self, view):
#         repl = self.repl(view)
#         if not repl:
#             return
#         view = repl.view
#         sel = view.sel()[0]
#         if sel.end() != sel.begin() or sel.end() != view.size():
#             return
#         last = view.substr(sublime.Region(view.size() - 1, view.size()))
#         if last != "\n":
#             return
#         repl.send()


# class OpenReplCommand(sublime_plugin.WindowCommand):
#     def run(self, cmd):
#         window = self.window
#         r = SublimeRepl(window, cmd)
#         repls[r.view.id()] = r

# import sys
# if __name__ == "__main__":
#     q = Queue.Queue()
#     sr = SubprocessRepl()#"python -i ")
#     r = Reader(sr, q)
#     w = Writer(q)
#     r.start()
#     w.start()
#     while True:
#         if not sr.working():
#             break
#         d = raw_input()
#         if not d:
#             if not sr.working():
#                 break
#             sr.write("\n")
#             continue
#         sr.write(d + "\n")
#     raw_input("All exit")
