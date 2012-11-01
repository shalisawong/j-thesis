net = require('net')

client = (host,port,interval,runLength) ->
    console.log("opening connection to #{host} #{port}")
    conn = net.createConnection(port,host)
    ping = ->
        conn.write("ping #{Date.now()}")
        process.stdout.write('.')
    intervalId = setInterval(ping,interval)
    clear = ->
        clearInterval(intervalId)
        console.log("\nclosing connection")
        conn.end()
        process.exit()
    setTimeout(clear,runLength)
server = ->
    net.createServer (stream) ->
        stream.on 'connect',     -> console.log('client connected')
        stream.on 'data', (data) -> stream.write(data)
        stream.on 'end',         -> console.log('client disconnected')

[node,script,type,port,rest...] = process.argv

if type is 'client'
    [host,interval,runLength] = rest
    client(host,port,interval,runLength)
else if type is 'server'
    server().listen(port)
else
    console.log("invalid type: #{type}")

