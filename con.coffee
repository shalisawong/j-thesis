net = require('net')

stdin = process.openStdin()
stdin.setEncoding('utf8')

stdin.on 'data',(input) -> dispatch(input)
stdin.on 'end', ()		-> console.log('bye\n')

clients = []
findClient = (name) ->
	for client in clients
		if client.name is name
			return client
	return null

process.stdout.write('> ')
dispatch = (input) ->
	[cmd,rest...] = input.split('\n')[0].split(' ')
	if cmd is 'clients'
		for client in clients when client.active
			console.log("#{client.name} (#{client.ip} #{client.hostPort})")
	else if cmd is 'host'
		clientName = rest[0]
		servType = rest[1]
		client = findClient(clientName)
		if client?
			client.stream.write("host #{servType}")
			console.log("#{clientName} is hosting a #{servType} server")
		else
			console.log("client not found")
	else if cmd is 'unhost'
		clientName = rest[0]
		client = findClient(clientName)
		if client?
			client.stream.write("unhost")
			console.log("#{clientName} is no longer hosting")
		else
			console.log("client not found")
	else if cmd is 'update'
		name = rest[0]
		console.log("updating #{name}")
	else if cmd is 'logs'
		console.log('logs')
	else if cmd is 'connect'
		[cliName1,cliName2,type] = rest
		cli1 = findClient(cliName1)
		cli2 = findClient(cliName2)
		if cli1? and cli2?
			cli1.stream.write("connect #{type} #{cli2.ip} #{cli2.hostPort}")
		else
			console.log("client(s) not found")
	else if cmd is 'record'
		clientName = rest[0]
		ip = rest[1]
		client = findClient(clientName)
		if client?
			client.stream.write("record #{ip} #{Date.now()}")
			console.log("#{clientName} is recording")
		else
			console.log("client not found")
	else if cmd is 'recordStop'
		clientName = rest[0]
		ip = rest[1]
		client = findClient(clientName)
		if client?
			client.stream.write("recordStop")
			console.log("#{clientName} is no longer recording")
		else
			console.log("client not found")
	else if cmd is 'run'
		[cliName1,cliName2,type] = rest
		cli1 = findClient(cliName1)
		cli2 = findClient(cliName2)
		timestamp = Date.now()
		if cli1? and cli2?
			cli1.stream.write("record #{cli2.ip} #{timestamp}")
			cli2.stream.write("record #{cli1.ip} #{timestamp}")

			setTimeout (() -> cli2.stream.write("host #{type}")),1000
			setTimeout (() ->
				cli1.stream.write("connect #{type} #{cli2.ip} #{cli2.hostPort}")),2000

			setTimeout (() -> cli2.stream.write("unhost")),50000
			setTimeout (() ->
				cli1.stream.write("recordStop")
				cli2.stream.write("recordStop")),53000
		else
			console.log("client(s) not found")
	else if cmd.length > 0
		console.log("ERROR: command #{cmd} not found")
	process.stdout.write('> ')

server = net.createServer (stream) ->
	client =
		name: 'GUEST'
		stream: stream
		ip: stream.remoteAddress
		active: yes
		hostPort: ''

	stream.setEncoding('utf8')
	stream.on 'connect', () ->
		console.log('client connected')
		process.stdout.write('> ')
		stream.write('giveName')
		clients.push client
	stream.on 'data', (data) ->
		[cmd,rest...] = data.split('\n')[0].split(' ')
		if cmd is 'name'
			client.name = rest.join(' ')
		else if cmd is 'exit'
			client.active = no
		else if cmd is 'hostPort'
			client.hostPort = rest[0]
			
	stream.on 'end', () ->
		stream.write("client '#{client.name}' disconnected")
server.listen(51231)

