# Simply merged `pry_repl.rb` from the Ruby REPL and - https://github.com/doitian/rails-console-pry

require 'rubygems'

use_rails_bundler = ENV["REPL_USE_RAILS_BUNDLER"] && !!(ENV["REPL_USE_RAILS_BUNDLER"].downcase =~ /^(true|t|yes|y|1)$/i)
if use_rails_bundler
    require 'bundler'
    begin 
        # Set up load paths for all bundled gems 
        ENV["BUNDLE_GEMFILE"] = "Gemfile"
        Bundler.setup 
    rescue Bundler::GemNotFound 
        raise RuntimeError, "Bundler couldn't find some gems.\n" + "Did you run `bundle install`?" 
    end
end

gem 'pry'
require 'pry'
require 'thread'
require 'json'
require 'pry-rails/version'
pry_rails_path = Gem.loaded_specs['pry-rails']

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

ENV['RAILS_ENV'] = "development"

APP_PATH = File.expand_path('config/application')
require APP_PATH

if ::Rails::VERSION::MAJOR >= 3
  class ::Rails::Console
  end
end

ARGV.unshift "console"

$: << File.join(pry_rails_path.full_gem_path, 'lib')
require 'pry-rails'

require 'rails/commands'

