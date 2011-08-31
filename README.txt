1) Signals:
	a) Pick signal from QuickPanel (fallback)
		subprocess_repl_send_signal, {}
	b) Specify signal by name:
		subprocess_repl_send_signal, {"signal": "SIGTERM"}
	c) Specify signal by code (verified)
		subprocess_repl_send_signal, {"signal": 3}
	