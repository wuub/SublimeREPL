"""
## Eval session
req {'id': '49305ed8-43dd-434b-9dad-e9567777bdf5', 'op': 'clone'}
res {'status': ['done'], 'new-session': '[eval-id]', 'session': 'b4ed3ed0-9d34-4a0f-97ee-f496c8f32733', 'id': '49305ed8-43dd-434b-9dad-e9567777bdf5'}

## Autocomplete session
req {'id': 'd3fe6e5c-5c1d-461a-a163-a8e464ce5fca', 'op': 'clone'}
res {'status': ['done'], 'new-session': '876e2b52-81f3-4c0f-9df4-3469b9d05642', 'session': '655ec0b4-9ffa-44f1-8392-791d48441987', 'id': 'd3fe6e5c-5c1d-461a-a163-a8e464ce5fca'}


## init repl
req {'session': '[eval-id]', 'code': '(do (defmacro set-signal-handler! [signal f] (if (try (Class/forName "sun.misc.Signal") (catch Throwable e)) (clojure.core/seq (clojure.core/concat (clojure.core/list (quote try)) (clojure. (...) "Unable to initialize completions."))))) (clojure.core/in-ns (quote user)) (help) nil) nil nil))', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'op': 'eval'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': 'REPL-y 0.1.0-beta10\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': 'Clojure 1.4.0\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '    Exit: Control+D or (exit) or (quit)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': 'Commands: (user/help)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '    Docs: (doc function-name-here)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '          (find-doc "part-of-name-here")\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '  Source: (source function-name-here)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '          (user/sourcery function-name-here)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': ' Javadoc: (javadoc java-object-or-class-here)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': 'Examples from clojuredocs.org: [clojuredocs or cdoc]\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '          (user/clojuredocs name-here)\n'}
res {'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'out': '          (user/clojuredocs "ns-here" "name-here")\n'}
res {'session': '[eval-id]', 'ns': 'user', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf', 'value': 'nil'}
res {'status': ['done'], 'session': '[eval-id]', 'id': '9199d3aa-f8cd-4057-a19d-90d3b16d3caf'}
req {'session': '[eval-id]', 'code': '', 'id': '07eba65f-2fd7-4f65-b2aa-6434f42568bb', 'op': 'eval'}
res {'status': ['done'], 'session': '[eval-id]', 'id': '07eba65f-2fd7-4f65-b2aa-6434f42568bb'}



req {'session': '3d90108f-96cf-4b46-b0ca-e9f0c3379b5e', 'code': '(print 12)\n', 'id': 'a7f2d6dd-5d21-48c5-8efe-f5b47be47931', 'op': 'eval'}
res {'session': '3d90108f-96cf-4b46-b0ca-e9f0c3379b5e', 'id': 'a7f2d6dd-5d21-48c5-8efe-f5b47be47931', 'out': '12'}
res {'session': '3d90108f-96cf-4b46-b0ca-e9f0c3379b5e', 'ns': 'user', 'id': 'a7f2d6dd-5d21-48c5-8efe-f5b47be47931', 'value': 'nil'}
res {'status': ['done'], 'session': '3d90108f-96cf-4b46-b0ca-e9f0c3379b5e', 'id': 'a7f2d6dd-5d21-48c5-8efe-f5b47be47931'}
user=> (print 12)
12nil



req {'session': 'dafe0e50-9d04-424a-bc60-2931fd7b5952', 'code': '\n\n(Thread/sleep 10000)\n', 'id': '238b2f00-255d-4f44-ae75-703012d23130', 'op': 'eval'}
req {'interrupt-id': '238b2f00-255d-4f44-ae75-703012d23130', 'session': 'dafe0e50-9d04-424a-bc60-2931fd7b5952', 'op': 'interrupt'}
res {'status': ['interrupted'], 'session': 'dafe0e50-9d04-424a-bc60-2931fd7b5952', 'id': '238b2f00-255d-4f44-ae75-703012d23130'}
res {'status': ['done'], 'session': 'dafe0e50-9d04-424a-bc60-2931fd7b5952'}
res {'status': ['done'], 'session': 'dafe0e50-9d04-424a-bc60-2931fd7b5952', 'id': '238b2f00-255d-4f44-ae75-703012d23130'}

"""

import uuid
import socket
import bencode
import bdecode

class Connection(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._sessions = {}


    def new_session(self):
        pass


class Session(object):
    def __init__(self, connection, session_id):
        pass

class Task(object):
    def __init__(self, session):
        pass

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 10001))

    s.sendall(bencode.bencode( {'id': str(uuid.uuid4()), 'op': 'clone'}))
    sf = s.makefile()
    recv = bdecode.load(sf)
    sess = recv["new-session"]

    ns = "user"
    while True:
        code = raw_input(ns + ">>> ")
        code_id = str(uuid.uuid4())
        req = {'session': sess, 'code': code + '\n', 'id': code_id, 'op': 'eval'}
        s.sendall(bencode.bencode(req))
        while True:
            one = bdecode.load(sf)
            if "out" in one:
                print one["out"]
                continue
            elif "err" in one:
                print one["err"]
                continue
            elif "ns" in one:
                ns = one["ns"]
                print one["value"]
                continue
            print one
            break




if __name__ == '__main__':
    main()
