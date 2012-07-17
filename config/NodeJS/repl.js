(function () {

    var repl = require('repl');
    
    repl.start({
        prompt:    null, //'> ',
        source:    null, //process.stdin,
        eval:      null, //require('vm').runInThisContext,
        useGlobal: true, //false
        useColors: false
    });

})();