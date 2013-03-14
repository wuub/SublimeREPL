require 'rubygems'
gem 'pry'
require 'pry'
require 'socket'
require 'thread'
require 'json'

include Socket::Constants

class PryInput
    def readline(prompt)
        $stdout.print prompt
        $stdout.flush
        $stdin.readline
    end
end

class PryOutput
    def puts(data="")
        $stdout.puts(data.gsub('`', "'"))
        $stdout.flush
    end
end

Pry.config.input = PryInput.new()
Pry.config.output = PryOutput.new()
Pry.config.color = false
Pry.config.editor = ARGV[0]
Pry.config.auto_indent = false
Pry.config.correct_indent = false

port = ENV["SUBLIMEREPL_AC_PORT"].to_i

socket = Socket.new(AF_INET, SOCK_STREAM, 0)
sockaddr = Socket.pack_sockaddr_in(port, '127.0.0.1')
socket.connect(sockaddr)
completer = Pry::InputCompleter.build_completion_proc(binding)

def read_netstring(s)
    size = 0
    while true
        ch = s.recvfrom(1)[0]
        if ch == ':'
            break
        end
        size = size * 10 + ch.to_i
    end
    msg = ""
    while size != 0
        msg += s.recvfrom(size)[0]
        size -= msg.length
    end
    ch = s.recvfrom(1)[0]
    return msg
end

# Thread.abort_on_exception = true
t1 = Thread.new do
    while true
        data = read_netstring(socket)
        req = JSON.parse(data)
        line = req["line"]
        completions = completer.call(req["line"])
        response = [line, completions]
        response_msg = JSON.dump(response)
        payload = response_msg.length.to_s + ":" + response_msg + ","
        socket.write(payload)
    end
end


Pry.start self
