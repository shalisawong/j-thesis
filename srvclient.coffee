net = require('net')

s = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

clients = {
    stream: ((host,port) ->
        conn = net.createConnection(port,host)
        i = 10000
        while i > 0
            i -= 1
            conn.write(s)
        conn.end()),
	echo: (host,port,interval,runLength) ->
		conn = net.createConnection(port,host)
		#conn.setNoDelay(noDelay=true) # disables TCP buffering algorithm
		intervalId = setInterval(( ->
			pingstr = "ping: #{Date.now()} "+("x" for item in [0...500]).join('')
			console.log("sending: #{pingstr[0...20]}")
			conn.write(pingstr)
			),interval)
		setTimeout(( ->
            clearInterval(intervalId)
            console.log("connection ended")
            conn.end()),runLength)
}

pad = (n,len) ->
	s = String(n)
	"0000000000"[0..len-s.length]+s

[node,script,type,host,port,rest...] = process.argv

if type is 'echo'
    [interval,runLength] = rest
    clients.echo(host,port,interval,runLength)
else if type is 'stream'
    clients.stream(host,port)
