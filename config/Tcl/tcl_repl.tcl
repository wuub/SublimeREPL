# http://pastebin.com/BtvLCWnk 
proc repl {} {
    set ::tcl_interactive 1
    while { $::tcl_interactive } {
        puts -nonewline "% "
        flush stdout
        set input [gets stdin]
        
        while { ![info complete $input] } {
            append input "\n" [gets stdin]
        }
            
        catch {namespace eval :: $input} result
        if { $result != "" } {
            puts $result
        }
    }
    return
}
repl
