# This code is modified Z_CLI.io from https://github.com/stevedekorte/io/blob/master/libs/iovm/io/Z_CLI.io 
Locals removeSlot("doFile")

DummyLine := File standardInput do(
    readLine := method(prompt,
        if(prompt, prompt print; File flush)
        resend
    )
)

CLI := Object clone do(
    prompt ::= "Io> "
    outPrompt ::= "==> "
    continuedLinePrompt ::= "... "

    isRunning ::= true # Get rid of this ...
    commandLineLabel ::= "Command Line" # and this?

    context ::= lazySlot(
        Lobby do(
            # Python-style underscore, stores the result of the previous computation.
            # Example:
            # Io> 1 + 1
            # ==> 2
            # Io> _ == 2
            # ==> true
            _ ::= nil

            exit := method(CLI stop)
        )
    )

    lineReader := lazySlot(
        # This might look as a `hack`, but why not use stdin as the default
        # reader, since it shares the same interface with Read(Edit)Line,
        # i.e. <reader> readLine.
        reader := DummyLine

        # Trying to use GNU ReadLine as the default line reader, falling
        # back to EditLine, if the attempt failed.
        try(reader := ReadLine) catch(Exception,
            try(reader := EditLine)
        )
        reader
    )

    # A list of error messages for the errors we understand.
    knownErrors := lazySlot(
        list("(", "[", "{", "\"\"\"", "(x,") map(error,
            self errorMessage(try(error asMessage) error)
        )
    )

    errorMessage := method(error, error beforeSeq(" on line"))

    doFile := method(path,
        System launchPath = if(Path isPathAbsolute(path),
            path
        ,
            System launchPath asMutable appendPathSeq(path)
        ) pathComponent

        System launchScript = path

        context doFile(path)
    )

    doLine := method(lineAsMessage,
        # Execute the line and report any exceptions which happened.
        executionError := try(result := context doMessage(lineAsMessage))
        if(executionError,
            executionError showStack
        ,
            # Write out the command's result to stdout; nothing is written
            # if the CLI is terminated, this condition is satisfied, only
            # when CLI exit() was called.
            if(isRunning,
                context set_(getSlot("result"))
                writeCommandResult(getSlot("result")))
        )
    )

    doIorc := method(
        # Note: Probably won't work on Windows, since it uses %HOMEPATH%
        # and %HOMEDRIVE% pair to indentify user's home directory.
        home := System getEnvironmentVariable("HOME")
        if(home,
            path := Path with(home, ".iorc")
            if(File with(path) exists,
                context doFile(path)
            )
        )
    )

    writeWelcomeBanner := method("Io #{System version}" interpolate println)
    writeCommandResult := method(result,
        outPrompt print

        if(exc := try(getSlot("result") asString println),
            "<exception while dislaying result>" println
            exc showStack
        )
    )

	stop := method(setIsRunning(false))

    interactive := method(
        # Start with the default prompt. The prompt is changed for continued lines,
        # and errors.
        prompt := self prompt
        line := ""
        # If there are unmatched (, {, [ or the command ends with a \ then we'll
        # need to read multiple lines.
        loop(
            # Write out prompt and read line.
            if(nextLine := lineReader readLine(prompt),
                # Add what we read to the line we've been building up
                line = line .. nextLine
            ,
                # Note: readLine method returns nil if ^D was pressed.
                context exit
                "\n" print # Fixing the newline issue.
            )

            compileError := try(
                lineAsMessage := line asMessage setLabel(commandLineLabel)
            )

            if(compileError,
                # Not sure that, displaying a different notification for
                # each error actually makes sense.
                if(nextLine size > 0 and errorMessage(compileError error) in(knownErrors),
                    prompt = continuedLinePrompt
                    continue
                )
                # If the error can't be fixed by continuing the line - report it.
                compileError showStack
            ,
                doLine(lineAsMessage)
            )

            return if(isRunning, interactive, nil)
        )
    )
)

CLI interactive
