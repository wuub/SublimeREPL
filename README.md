SublimeREPL for SublimeText (2 and 3)
=====================================

[![Stories in Ready](https://badge.waffle.io/wuub/SublimeREPL.png?label=ready)](http://waffle.io/wuub/SublimeREPL) 

If you would like to donate to support SublimeREPL development, you can do so using [GitTip](https://www.gittip.com/wuub/) or [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=4DGEPH7QAVHH6&lc=GB&item_name=SublimeREPL&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted). Someone willing to take care of documentation would also be very welcome :-)


Features
--------

#### Common
 * Run an interpreter (REPL) inside SublimeText2 view/tab.
 * Per-language persistent REPL history.
 * Easily evaluate code in the running REPL
 * Replace your current build system, and use stdin in your programs.
 * Rich configuration with platform specific settings, project/file dependent environment variables and sane defaults.

#### Python
 * Launch python in local or remote(1) virtualenv.
 * Quickly run selected script or launch PDB.
 * Use SublimeText2 Python console with history and multiline input.

(1) - (ssh, linux/osx only)

Screenshots
-----------
#### Running python code in SublimeREPL
![Running python code in SublimeREPL](http://i.imgur.com/mmYQ6.png)
#### R on Windows
![R on Windows](http://i.imgur.com/jjsDn.png)

Videos
------
 * ![Python & virtualenv over SSH](http://img.youtube.com/vi/zodAqBvKQm0/2.jpg)  [Python & virtualenv over SSH](http://youtu.be/zodAqBvKQm0)
 * ![SBT integration demo](http://img.youtube.com/vi/1Y7Mr_RJpmU/3.jpg) [SBT integration demo](http://youtu.be/1Y7Mr_RJpmU)


Installation
============

1. Install Package Control. [http://wbond.net/sublime_packages/package_control](http://wbond.net/sublime_packages/package_control)
2. Install SublimeREPL
 1. `Preferences | Package Control | Package Control: Install Package`
 2. Choose `SublimeREPL`
3. Restart SublimeText2
4. Configure `SublimeREPL` (default settings in `Preferences | Package Settings | SublimeREPL | Settings - Default` should be modified in `Preferences | Package Settings | SublimeREPL | Settings - User`, this way they will survive package upgrades!

Documentation
=============

Very basic documentation will soon be available on RTD: [http://sublimerepl.readthedocs.org/](http://sublimerepl.readthedocs.org/)

#### Getting started

* Create or open your file with code.
* Menu / Tools / Command Palette (OS X: `⇧⌘P`) 
then type "SublimeREPL" and select the approperiate language.
* Menu / View / Layout / Rows: 2 (OS X: `⌥⇧⌘2`).
* Menu / View / Move File to Group / Group 2 (`⌃⇧2`).

#### Keybindings

* Evaluate in REPL:
 * <kbd>ctrl+,</kbd>, <kbd>s</kbd> Selection
 * <kbd>ctrl+,</kbd>, <kbd>f</kbd> File  
 * <kbd>ctrl+,</kbd>, <kbd>l</kbd> Lines
 * <kbd>ctrl+,</kbd>, <kbd>b</kbd> Block
* Transfer in REPL (just copy, without evaluating it):
 * <kbd>ctrl+shift+,</kbd>, <kbd>s</kbd> Selection
 * <kbd>ctrl+shift+,</kbd>, <kbd>f</kbd> File  
 * <kbd>ctrl+shift+,</kbd>, <kbd>l</kbd> Lines
 * <kbd>ctrl+shift+,</kbd>, <kbd>b</kbd> Block

Note: <kbd>ctrl+,</kbd>, <kbd>f</kbd> means: press Ctrl and Comma, release all, press F.


License and Price
=================

Since version 1.2.0 SublimeREPL is licensed under GPL. Previous versions were licensed under BSD.
If you're using SublimeREPL in commercial environment a donation is strongly encouraged ;-)

Compatibility
================

SublimeREPL is developed against the latest dev build of SublimeText3.
Ubuntu 13.04 is main target platform with OSX closely after.
Windows is tested from time to time.

Sublime Text 2 compatibility is maintained where possible, but it's not a priority. 


FAQ
---

### 1. Is this a terminal emulator?

No. Shell (cmd.exe/bash) REPL can be used for simple tasks (file creation, `git init` etc.) but anything _terminal like_ (mc, vim) will not work! SublimeREPL has a sister project: [SublimePTY](https://github.com/wuub/SublimePTY) that aims to bring real terminal emulator to SublimeText2.

### 2. Is IPython supported?

Yes, with autocompletion and some windowed `%pylab`. Inline `%pylab` is unfortuneatly not possible right now.


