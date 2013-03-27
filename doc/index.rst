.. toctree::
   :maxdepth: 2

SublimeREPL
===========

SublimeREPL is a plugin for Sublime Text 2 that lets you run interactive
interpreters of several languages within a normal editor tab. It also allows
connecting to a running remote interpreter (e.g. Clojure/Lein) though a telnet
port.

SublimeREPL has a built-in support for command history and transferring code
from open buffers to the interpreters for evaluation, enabling interactive 
programming.

.. note::
   This documentation is work in progress. Details on language integrations are
   sorely missing. Please contribute!

Installation
------------

Download `Package Control`__, select Install Package and pick SublimeREPL from the list of 
available packages. You should have Package Control anyway.

__  http://wbond.net/sublime_packages/package_control


Quick Start
-----------

SublimeREPL adds itself as a submenu in Tools. You can choose any one of the
preconfigured  REPLs and  if it's available in your SYSTEM PATH [#]_, it will
be launched immediately.

.. image:: _static/menu.png

Second and more user friendly way to launch any given REPL is through Command
Palette. Bring up Command Palette and type "repl". You will be presented with
all preconfigured REPLs. Running REPL through Command Palette has exactly the
same result as picking it from *Tools > SublimeREPL* menu.

.. image:: _static/palette.png

.. [#] One of the most frequently reported errors is SublimeREPL not being able
   to find interpreter executable, even if it's visible in your shell. There are several way to fix this problem that we'll discuss in FAQ. 


Keyboard shortcuts
------------------

The default shortcuts shipped with SublimeREPL are listed below. If you are
accustomed to another REPL keymap, or if you intend to work in REPL a lot
(lispers pay attention!) you may want to rebind the keys more to your liking.

REPL keys
^^^^^^^^^

.. NOTE::
   The list below omits the trivial text editing keybindings (e.g. left, right
   etc). They are nevertheless configurable in keymap files.

+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Linux         | OS X          | Windows        | Command used                     | Meaning                                         |
+===============+===============+================+==================================+=================================================+
| Up            | Up            | Up             | repl_view_previous               | Walk back to previous input, with autocomplete  |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Alt+p         | Ctrl+p        | Alt+p          | repl_view_previous               | Walk back to previous input, no autocomplete    |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Down          | Down          | Down           | repl_view_next                   | Walk back to next input, with autocomplete      |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Alt+n         | Ctrl+n        | Alt+n          | repl_view_next                   | Walk back to next input, no autocomplete        |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Enter         | Enter         | Enter          | repl_enter                       | Send current line to REPL                       |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Esc           | Esc           | Esc            | repl_escape                      | Clear REPL input                                |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Ctrl+l        | Ctrl+l        | Shift+Ctrl+c   | repl_clear                       | Clear REPL screen                               |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+
| Shift+Ctrl+c  | Shift+Ctrl+c  | *Unsupported*  | subprocess_repl_send_signal      | Send SIGINT to REPL                             |
+---------------+---------------+----------------+----------------------------------+-------------------------------------------------+

Source buffer keys
^^^^^^^^^^^^^^^^^^

.. important::
   The keybindings here use Ctrl+, as a prefix (C-, in emacs notation), meaning press Ctrl, press comma, release both. Pressing the
   prefix combination and then the letter will immediately send the target text into the REPL and *evaluate* it as if you pressed enter.
   If you want to prevent evaluation and send the text for *editing* in the REPL, press Shift with the prefix combination. 

.. note::
    Default source buffer keys are identical on all platforms.

+---------------+--------------------------------------------------------------------------------------------------------------------+
| Key           | Meaning                                                                                                            |
+===============+====================================================================================================================+
| Ctrl+, b      | Send the current "block" to REPL. Currently Clojure-only.                                                          |
+---------------+--------------------------------------------------------------------------------------------------------------------+
| Ctrl+, s      | Send the selection to REPL                                                                                         |
+---------------+--------------------------------------------------------------------------------------------------------------------+
| Ctrl+, f      | Send the current file to REPL                                                                                      |
+---------------+--------------------------------------------------------------------------------------------------------------------+
| Ctrl+, l      | Send the current line to REPL                                                                                      |
+---------------+--------------------------------------------------------------------------------------------------------------------+

Language specific information 
-----------------------------
 
SublimeREPL's integration with a specific language includes language-specific
main menu and palette options for REPL startup, keymaps, and special REPL
extensions unique to the target language. An integration may contain several
different REPL modes which are based  on different underlying classes.

Clojure
^^^^^^^

The Clojure backend supports Leiningen projects. To start a REPL with
Leiningen project environment, open your `project.clj` and use the menu or the
command palette to start the REPL while the project file is currently open.

If your Leiningen installation is not system-global, you may need to tweak your
configuration so that SublimeREPL can find your lein binary::

    "default_extend_env": {"PATH": "{PATH}:/home/myusername/bin"}

Additionally, the Clojure backend has a telnet mode that can connect to an
existing REPL by asking for a TCP port number  on the local machine.
Unfortunately, the feature that automagically determines port numbers from the
project file no longer works with Leiningen 2 projects. For now, port numbers
can only be specified manually.

The source buffer "send block" command (Ctrl+, b) deserves a special mention.
Performing this command while the cursor is within the body of a definition
will select this  (current, top-level) definition and send it to the REPL for
evaluation. This means that the latest version of the function you're
currently working on will be installed in the live environment so  that you
can immediately start playing with it in the REPL. This is similar to [slime-]eval-defun
in emacs.

Additional keybindings are available for Clojure:

+---------------+--------------------------------------------------------------------------------------------------------------------+
| Key           | Meaning                                                                                                            |
+===============+====================================================================================================================+
| Ctrl+F12 c s  | Launch a subprocess Clojure REPL                                                                                   |
+---------------+--------------------------------------------------------------------------------------------------------------------+
| Ctrl+F12 c t  | Connect to a running Clojure REPL                                                                                  |
+---------------+--------------------------------------------------------------------------------------------------------------------+

Python
^^^^^^

Both stock Python and Execnet backends support virtualenv. Various ways to work with Python, including PDB and IPython, are supported.

Documentation contributions from a Python specialist are welcome.

Configuration
-------------

The default SublimeREPL configuration documents all available configuration settings.

Frequently Asked Questions
--------------------------

I'm trying to launch a REPL and I am getting a pop up dialog saying OSError(2, 'No such file or directory')
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sublime is unable to locate the binary that is needed to launch your REPL. If the binary is not in your system 
path, tweak the configuration::

    "default_extend_env": {"PATH": "{PATH}:/home/myusername/bin"}

I'd like an interactive REPL for Foo and it is not supported, what do?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Chances are, you only need a minimal amount of work to add an integration, and necessary steps are described
here briefly. 

If you already have an  interactive shell for Foo, you can use the subprocess
REPL. For an example, see PHP or Lua integration in `config/PHP`.

If Foo provides an interactive environment over TCP, you can use the telnet
REPL. For an example, see MozRepl integration

Supported languages
-------------------

SublimeREPL currently ships with support for the following languages:

* Clisp
* Clojure
* CoffeeScript
* Elixir
* Execnet Python 
* Erlang
* F#
* Groovy
* Haskell
* Lua
* Matlab
* MozRepl
* NodeJS
* Octave
* Perl
* PHP interactive mode
* PowerShell
* Python
* R
* Racket
* Ruby
* Scala
* Scheme
* Shell (Windows, Linux and OS X)
* SML
* Sublime internal REPL (?)
* Tower (CoffeeScript)

Plugin structure
----------------

SublimeREPL implements five different types of REPLs which are based on an abstract REPL class:

* Subprocess-based REPLs. The process running in the REPL is a subprocess of the editor. The input and
  output of the process is connected to the output and the input of the REPL
* Telnet-based REPLs. The process runs outside of the editor, presumably having been spawned
  externally or daemonized, and the REPL connects to it via minimal telnet protocol.
* PowerShell REPLs. These are only used by PowerShell integration.
* Execnet REPLs. These are only used by Execnet Python integration
* Sublime REPLs.

A concrete language integration is *configuration* that specifies one of these REPL classes as the base. 
Most integrations use the subprocess-based REPL.