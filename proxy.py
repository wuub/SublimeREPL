import socket
import bdecode
import bencode
import Queue
import threading
import time


class Fwd(threading.Thread):
    def __init__(self, src, dst, tag):
        super(Fwd, self).__init__()
        self.src = src
        self.dst = dst
        self.tag = tag

    def run(self):
        f = self.src.makefile()
        buf = bdecode.Peekaboo(f)
        while True:
            one = bdecode.decode_one(buf)
            print self.tag, one
            self.dst.sendall(bencode.bencode(one))


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind(("localhost", 10000))
    s.listen(1)

    (cli, addr) = s.accept()

    p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p.connect(("localhost", 53852))

    fwd = Fwd(cli, p, "req")
    back = Fwd(p, cli, "res")

    fwd.start()
    back.start()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
