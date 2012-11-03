#! encoding: utf-8


class Peekaboo(object):
    def __init__(self, f):
        self._f = f
        self._n = None

    def peek(self):
        if self._n is None:
            self._n = self._f.read(1)
        return self._n

    def read(self, n):
        left = n
        buf = []
        if self._n:
            buf.append(self._n)
            self._n = None
            left -= 1
        while True:
            if left == 0:
                break
            chunk = self._f.read(left)
            left -= len(chunk)
            buf.append(chunk)
        return "".join(buf)


def decode_int(wrapper):
    assert wrapper.read(1) == 'i'

    sign = 1
    if wrapper.peek() == '-':
        sign = -1
        wrapper.read(1)

    num = 0
    while True:
        ch = wrapper.read(1)
        if '0' <= ch <= '9':
            num = 10 * num + (ord(ch) - ord('0'))
        elif ch == 'e':
            break
        else:
            raise ValueError('unexpected char in decode_int %s' % ch)
    return sign * num


def decode_str(wrapper):
    num = 0
    while True:
        ch = wrapper.read(1)
        if ch == ":":
            break
        num = 10 * num + (ord(ch) - ord('0'))
    res = wrapper.read(num)
    return res


def decode_list(wrapper):
    assert wrapper.read(1) == 'l'
    res = []
    while True:
        ch = wrapper.peek()
        if ch == 'e':
            wrapper.read(1)
            break
        res.append(decode_one(wrapper))
    return res


def decode_dict(wrapper):
    assert wrapper.read(1) == 'd'
    res = {}
    while True:
        ch = wrapper.peek()
        if ch == 'e':
            wrapper.read(1)
            break
        key = decode_str(wrapper)
        value = decode_one(wrapper)
        res[key] = value
    return res


def decode_one(wrapper):
    ch = wrapper.peek()
    if ch == 'i':
        return decode_int(wrapper)
    if '0' <= ch <= '9':
        return decode_str(wrapper)
    if ch == 'l':
        return decode_list(wrapper)
    if ch == 'd':
        return decode_dict(wrapper)


def loads(s):
    sio = StringIO.StringIO(s)
    buf = Peekaboo(sio)
    return decode_one(buf)

def load(f):
    buf = Peekaboo(f)
    return decode_one(buf)


if __name__ == '__main__':
    import bencode
    import StringIO

    def test(d):
        s = bencode.bencode(d)
        sio = StringIO.StringIO(s)
        buf = Peekaboo(sio)
        #w = Wrapper(io)
        out = decode_one(buf)
        assert d == out, "%s %s" % (d, out)

    test(1)
    test(12123123)
    test("abc")
    test("safdasdfasdfqwefsdfqwfe")

    test([1, 2, 3, 4, 5])

    test([])

    test({})
    test({"hello": 12})
    test(-12)
    test(0)
    test(-1)

    test(u"zażółć".encode("utf-8"))

    print "ok"
