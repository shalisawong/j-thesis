
'''
	Returns the number of nodes that are relays, non-relays, and a dictionary of {nodes:number 
	occurances} in the scallion.log. Allows to pick relay with most cells going through.
'''
def info_scallion():
	with open("scallion10.log", "r") as f:
		nodes = {}
		relay = 0
		non_relay = 0

		for line in f:

			split = line.split() # split the log
			if "CLIENTLOGGING" in line:
				name = split[4].split("-")[0].replace("[", "") 
				if "relay" in name:
					relay += 1
				else:
					non_relay += 1
			
				if name not in nodes: 
					nodes[name] = 1
				else:
					num = nodes.get(name) + 1
					nodes[name] = num


		print "relay:", relay
		print "non-relay:", non_relay
		print nodes


'''
	Returns the number of circuits for a given file -- tor_fmt_...log
'''
def num_circuits():

	circs = []
	with open("tor_fmt_relayguard2.log", "r") as f:
		for line in f:
			split = line.split()
			circ = split[-1]
			if (circ == '0'):
				print line, split
			if circ not in circs:
				circs.append(circ)
		print "Number of circuits:", len(circs)
		print circs	

#info_scallion()	
num_circuits()


'''
7/23/14
for scallion_10.log pre create/destroy fix

relay: 1137381
non-relay: 42
create-destroy total: 8500
create-destroy non-relay: 42
{'relaymiddle3': 6, 'relayguard5': 5845, 'relaymiddle5': 243253, '4uthority1': 42, 'relaymiddle8': 4, 'relaymiddle9': 4, 'relayexit1': 108, 'relaymiddle7': 4, 'relaymiddle4': 4, 'relayguard1': 41455, 'relaymiddle1': 216, 'relayguard3': 4183, 'relayguard2': 285855, 'relayexitguard1': 1677, 'relayguard4': 856, 'relaymiddle6': 4, 'relaymiddle2': 553907}


7/24/14
for scallion_10.log post fix

the scallion_10.log pre-logshadow.py 

relay: 1423781
non-relay: 0
{'relayexitguard1': 47, 'relaymiddle5': 227106, 'relayguard1': 36659, 'relaymiddle1': 74, 'relayguard3': 25213, 'relayguard2': 660112, 'relayguard5': 2915, 'relayguard4': 1644, 'relaymiddle2': 470011}

Number of circuits: 205
['1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '1a', '1b', '1c', '1d', '1e', '1f', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '2a', '2b', '2c', '2d', '2f', '30', '31', '32', '33', '35', '36', '37', '38', '39', '3a', '3b', '3c', '3d', '3e', '3f', '40', '41', '42', '43', '45', '44', '46', '47', '48', '49', '4a', '4b', '4c', '4d', '4e', '4f', '50', '52', '53', '54', '55', '56', '57', '59', '58', '5a', '5b', '5e', '5f', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '6a', '6b', '6c', '6d', '6e', '6f', '71', '72', '73', '74', '75', '76', '77', '78', '79', '7a', '7b', '7c', '7d', '7f', '80', '7e', '81', '82', '83', '84', '85', '86', '87', '88', '89', '8a', '8b', '8c', '8d', '8e', '8f', '91', '92', '93', '94', '96', '97', '98', '99', '9a', '9b', '9e', '9d', '9f', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'aa', 'ab', 'ac', 'ad', 'ae', 'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b8', 'b9', 'ba', 'bb', 'bc', 'bd', 'bf', 'c0', 'c2', 'c4', 'c5', 'c6', 'c8', 'c7', 'c9', 'ca', 'cb', 'cc', 'cd', 'ce', 'cf', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd9', 'db', 'da', 'dc']



'''

