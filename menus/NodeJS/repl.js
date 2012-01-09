(function(){
	var options = {
		prompt:     null, //'> ',
		source:     null, //process.stdin,
		eval:       null, //require('vm').runInThisContext,
		useGlobal:  true  //false
	};

	var repl = require('repl');
	repl.disableColors = true;
	repl.start(options.prompt, options.source, options.eval, options.useGlobal);
})();