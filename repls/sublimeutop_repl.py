# encoding: utf-8
from __future__ import absolute_import, print_function, division

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from .subprocess_repl import SubprocessRepl

class SublimeUTopRepl(SubprocessRepl):
    TYPE = "sublime_utop"

    def __init__(self, encoding, **kwds):
        super(SublimeUTopRepl, self).__init__(encoding, apiv2=True, **kwds)

        # Buffer for reassembling stanzas arrived from utop.
        self._buffer = b''

        # Phrase pending input with mapping of utop-lines to
        # SublimeREPL-view-lines.
        self._phrase = []
        self._phrase_line_begins = []

        # Completion state.
        self._completions = None
        self._completion_prefix = ""
        self._completion_queue = Queue()

    def autocomplete_available(self):
        return True

    def autocomplete_completions(self, whole_line, pos_in_line,
                                 prefix, whole_prefix, locations):
        self._completion_prefix = prefix
        self.write_command('complete', '', [whole_prefix])

        # This would block the UI. When REPL works correctly,
        # this blocks for less than 100ms.
        return [(x, x) for x in self._completion_queue.get(timeout=500)]

    #
    # USER INTERACTION LEVEL
    #
    # User interaction consists of visible artifacts (prompt, etc)
    # and input in form of complete expressions. History is handled
    # by SublimeREPL.
    #

    def compose_highlights(self, a, b):
        highlights = []

        # Highlight each fragment of line which lies in [a;b).
        for (line, loc) in zip(self._phrase, self._phrase_line_begins):
            # Does this line have any highlight?
            if a < len(line):
                # Yeah, does it end here?
                if b <= len(line):
                    # Highlight the requested area and return.
                    highlights.append((loc + a, loc + b))
                    break
                else:
                    # Highlight till the end of line.
                    highlights.append((loc + a, loc + len(line)))

            # Shift the highlight region left by len(line) and
            # continue.
            a -= len(line) + 1
            b -= len(line) + 1
            # Always start from beginning of line for next lines.
            if a < 0:
                a = 0

        return [('highlight', x) for x in highlights]

    def read(self):
        stanza = self.read_stanza()
        if stanza is None:
            return None

        key, value = stanza
        if key == 'accept':
            packet = []

            if value != "":
                a, b = map(int, value.split(','))
                packet.extend(self.compose_highlights(a, b))

            # We've finished this phrase.
            self._phrase = []
            self._phrase_line_begins = []

            # Erase prompt. Accept is the first stanza we receive in
            # reply to input; immediately after it may follow stdout/stderr
            # and prompt stanzas in any order. To avoid garbled text,
            # we need to erase prompt before continuing.
            packet.append(('prompt', ''))
            packet.append(('output', '\n'))
            return packet

        elif key == 'stdout':
            return [('output', value + '\n')]
        elif key == 'stderr':
            return [('output', '! ' + value + '\n')]

        elif key == 'prompt':
            return [('prompt', '# ')]
        elif key == 'continue':
            return [('prompt', '\n  ')]

        # Full completion reply is completion-start..completion*..completion-end.
        # Names are fully qualified, i.e. Thread.
        elif key == 'completion-start':
            self._completions = []
            return []
        elif key == 'completion':
            self._completions.append(value)
            return []
        elif key == 'completion-stop':
            self._completion_queue.put(self._completions)
            self._completions = None
            return []

        # Word completion reply is just completion-word stanza.
        # Names are partial, i.e. ead ([Thr]ead).
        elif key == 'completion-word':
            self._completion_queue.put([self._completion_prefix + value])
            return []

        # Stuff we don't care about: phrase-terminator.
        # Stuff we never receive: history-*.
        else:
            return []

    def write(self, expression, location=None):
        # If the phrase is incomplete, utop will not remember it, so
        # we need to account for it here. Also, Shift+Enter will add a literal
        # newline, which would otherwise break protocol.
        for line in expression.split('\n'):
            self._phrase.append(line)
            if location is not None:
                self._phrase_line_begins.append(location)
                location += len(line) + 1

        self.write_command('input', 'allow-incomplete', self._phrase)

    #
    # COMMAND LEVEL
    #
    # A command is a collection of stanzas: one begin stanza,
    # zero or more data stanzas, and one end stanza.
    #

    def write_command(self, command, options, data):
        self.write_stanza(command, options)
        for datum in data:
            self.write_stanza('data', datum)
        self.write_stanza('end')

    #
    # STANZA LEVEL
    #
    # A stanza is a statement of form "key:value\n".
    # Decoding and encoding is done on the stanza level.
    #

    def read_stanza(self):
        while True:
            try:
                stanza_end = self._buffer.index(b'\n')
                stanza = self.decoder.decode(self._buffer[:stanza_end])
                self._buffer = self._buffer[stanza_end+1:]

                colon = stanza.index(':')
                return stanza[:colon], stanza[colon+1:]
            except ValueError:
                bytes = self.read_bytes()
                if not bytes:
                    return None
                else:
                    self._buffer += bytes

    def write_stanza(self, key, value=''):
        (bytes, _) = self.encoder(key + ':' + value + '\n')
        self.write_bytes(bytes)
