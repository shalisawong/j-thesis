net = require('net')
exec = require('child_process').exec

servPort = 41231

servers =
	echo: net.createServer (stream) ->
		stream.setNoDelay(noDelay=true)
		stream.on 'data', (data) ->
			#stream.write(data)
			console.log("received: #{data[0...(if data.length < 20 then data.length else 20)]} (#{data.length})")
		stream.on 'end', () ->
	stream: net.createServer (stream) ->
		stream.on 'end', ->
			console.log('stream ended')

servTypes = ['echo','stream']
localIp = process.argv[2] || '127.0.0.1'

procs = []

controlPort = process.argv[5] or 51231
controlAddr = process.argv[4] or '129.133.8.19' # kurtz.cs.wesleyan.edu
if process.argv[3] == 'tor'
	useTor = true
else
	useTor = false

conn = net.createConnection(controlPort,controlAddr)
conn.on 'data', (data) ->
	[cmd,rest...] = data.toString().split('\n')[0].split(' ')
	console.log("received: #{cmd}")
	if cmd is 'giveName'
		conn.write("name #{process.argv[2]}")
	else if cmd is 'host'
		servType = rest[0]
		console.log("starting #{servType} server...")
		servers[servType].on 'close', () -> console.log("#{servType} server stopped")
		servers[servType].listen(servPort)
		conn.write("hostPort #{servPort}")
	else if cmd is 'unhost'
		for servType in servTypes
			console.log("stopping #{servType} server...")
			#servers[servType].close()
	else if cmd is 'record'
		ip = rest[0]
		timestamp = rest[1]
		filename = "#{timestamp}_#{ip}_#{localIp}.data"
		child = exec "sudo tcpdump host #{ip} -w data/#{filename}",proc
		procs.push(child)
	else if cmd is 'recordStop'
		exec("sudo kill #{proc.pid}",->) for proc in procs
		procs = []
	else if cmd is 'connect'
		connType = rest[0]
		host = rest[1]
		port = rest[2]
		if useTor
			prefix = 'proxychains '
		else
			prefix = ''

		console.log("connecting to #{host} #{port}...")
		#conn(host,port,100,30000)
		child = exec "#{prefix}node srvclient.js #{connType} #{host} #{port} 100 30000",proc
	else
		console.log("unrecognized input: #{data.toString()}")

conn.on 'end', () ->
	conn.write('exit')

proc = (error,stdout,stderr) ->
	console.log("stdout: #{stdout}")
	console.log("stderr: #{stderr}")
	if error?
		console.log("ERROR: #{error}")
