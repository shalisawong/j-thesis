import sys, re, cPickle, random
'''
	syntax: python scallion_test.py infile option
			option = pre-fmt for info_scallion
				 post-fmt for num_circuits
'''

VALID_CIRCS = ['135', '1f0', '1fa', 'a4', '231', '14d', '197', '267', '10f', '170', 'eb', '1db', 'd4', '13c', '175', '266', '12d', '1f4', 'd3', '122', '1cc', '233', 'cb', '154', '2bd', '30b', '2a4', '1d7', '1cf', '70', '107', '1d3', '2d4', '198', '98', '234', 'ba', '1d0', '18c', '1e6', '17f', '31e', 'f0', '24e', '2fb', 'b2', 'f9', '132', '1b8', '119', 'ce', '147', '292', '8c', 'ab', '29f', 'b5', '168', '189', 'f4', '1dc', '16a', '89', '125', '25e', '115', '1ad', '141', '243', '28d', '29b', '229', '2cb', 'b7', 'aa', 'f5', '2ff', '21d', '17c', '29a', '113', '1fe', '140', '1a3', '20a', '2a0', 'd8', '289', 'ac', '19c', '5e', '169', '15b', '2fc', '1b4', 'de', '17d', '177', '25d', 'bc', '2de', 'fa', '130', '1bb', '8b', '296', '238', 'a6', '1a1', '241', '253', '18f', '163', '76', '15e', '286', '283', 'f7', '176', 'd0', '2ba', '1bc', '9c', '278', '25f', '23e', '260', '1da', '28e', 'e7', 'ad', '195', '2a3', '148', '1aa', '151', '18b', '105', '225', '110', '2bb', '223', '1ed', '2fe', '184', '131', '191', '2b6', '150', '80', '55', '2aa', '68', '11d', '20e', '249', '294', '219', '21e', '1eb', '207', '12f', 'd6', '193', '171', 'da', '6e', '12b', '2ea', 'bb', 'a1', '21f', '17e', '27f', '23c', '21c', '17b', '280', '1ee', 'e2', '117', '6c', '1c5', 'e6', '5d', '161', '162', '1e7', '331', 'f2', '221', '1f3', '1c3', '142', '2ce', '1a0', '1bf', '1f5', '13a', 'f8', '262', '305', '203', '12e', '275', '25c', '111', 'e8', '9a', 'c4', '4e', '22e', '50', '2c2', '205', '297', '1ff', '126', '182', '1c0', '10c', '185', '271', '235', '2d2', '92', '123', '1d5', '81', '302', '10b', '261', '181', '1a5', '2f0', '2d8', '2a1', 'd2', '1c8', '1c2', 'ef', '109', '29c', '1af', '226', 'ca', '158', '99', 'bf', '18d', '217', 'd7', 'c6', 'cc', 'c5'] 

'''
	Returns the number of nodes that are relays, non-relays, and a dictionary of {nodes:number 
	occurances} in the scallion.log. Allows to pick relay with most cells going through.
'''
def info_scallion(infile):
	with open(infile, "r") as f:
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
	Extracts the host name and ip addresses from scallion.log and 
	returns a dictionary of {circ_id:name}. Checks only valid circuits.
'''
def circuit_client_map(infile, nodename):

	ip_addresses = {}
	circuits = {}
	circ_name_map = {}

	with open(infile) as f:
		for line in f:

			# done in the beginning of scallion.log	
			if "Created Host" in line:

				ip = '(([0-9][0-9]?[0-9]?\\.){3}([0-9][0-9]?[0-9]?))'

				# find name and ip address of host
				try:
					name = re.search("'(.+?)'", line).group(1)
					ip_addr = re.search(ip, line).group(0)

				except AttributeError:
					print "'Created Host' found with either no host name or ip address."
					return
 
				ip_addresses[ip_addr] = name

			# go through circuits and map them to a client
			if nodename and "CLIENTLOGGING" in line:
				split = line.split()
				circ_id = split[-1]
				prev_ip = split[8]

				if circ_id in VALID_CIRCS and circ_id not in circuits:
						circuits[circ_id] = prev_ip
				
		for circ in circuits:
				name = ip_addresses[circuits.get(circ)]

				if name not in circ_name_map:
					circ_name_map[name] = [int(circ, 16)]
				elif name in circ_name_map:
					circ_list = circ_name_map.get(name)
					circ_list.append(int(circ, 16))
		
	with open("client_info.log", 'w') as client_log, open("rg2_50_parsed.pickle", 'r') as ident_log:
			records = cPickle.load(ident_log)

			for key in sorted(circ_name_map.iterkeys()):
					client_log.write( "%s: %s \n" % (key, circ_name_map[key]))

			# calculate number of circuits
			num_circs = 0
			for client in circ_name_map:
					num = len(circ_name_map.get(client))
					num_circs += num
			client_log.write("Number of Circuits: " + str(num_circs) + "\n")
			client_log.write("Number of Clients: " + str(len(circ_name_map)) + "\n")

			ident_list = []
			for record in records:
					ident = record['ident']
					ident_list.append(ident)
			client_log.write(str(ident_list))
	
			return circ_name_map, ident_list


if __name__ == "__main__":
	infile = sys.argv[1]
	option = sys.argv[2]
	
	if option == "pre-fmt":
		info_scallion(infile)	
	elif option == "circ-client-map":
		nodename = sys.argv[3]
		type_client = sys.argv[4]
		num_circs = int(sys.argv[5])

		circ_name_map, ident_list = circuit_client_map(infile, nodename)
		filt_circ_name_map = {k:v for (k,v) in circ_name_map.iteritems() if type_client in k}
		print filt_circ_name_map
		ident_string = ''
		repeat = []

		while num_circs > 0:
				client = random.choice(filt_circ_name_map.keys())
				circ = random.choice(circ_name_map.get(client))
				for item in ident_list:
						if item[0] == circ and item not in repeat:
								repeat.append(item)
								ident = "'" + str(item[0]) + "," + str(item[1]) + "' "
								ident_string += ident
								num_circs -= 1
		print ident_string

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


7/28/14
for scallion_10.log post CREATE fix

relay: 1245010
non-relay: 0
{'relayexitguard1': 12, 'relaymiddle5': 151002, 'relayguard1': 112855, 'relaymiddle1': 293, 'relayguard3': 2978, 'relayguard2': 235201, 'relayguard5': 3312, 'relayguard4': 679, 'relaymiddle2': 738678}

'''


'''
scallion50 valid circs 7/28/14

['135', '1f0', '1fa', 'a4', '231', '14d', '197', '267', '10f', '170', 'eb', '1db', 'd4', '13c', '175', '266', '12d', '1f4', 'd3', '122', '1cc', '233', 'cb', '154', '2bd', '30b', '2a4', '1d7', '1cf', '70', '107', '1d3', '2d4', '198', '98', '234', 'ba', '1d0', '18c', '1e6', '17f', '31e', 'f0', '24e', '2fb', 'b2', 'f9', '132', '1b8', '119', 'ce', '147', '292', '8c', 'ab', '29f', 'b5', '168', '189', 'f4', '1dc', '16a', '89', '125', '25e', '115', '1ad', '141', '243', '28d', '29b', '229', '2cb', 'b7', 'aa', 'f5', '2ff', '21d', '17c', '29a', '113', '1fe', '140', '1a3', '20a', '2a0', 'd8', '289', 'ac', '19c', '5e', '169', '15b', '2fc', '1b4', 'de', '17d', '177', '25d', 'bc', '2de', 'fa', '130', '1bb', '8b', '296', '238', 'a6', '1a1', '241', '253', '18f', '163', '76', '15e', '286', '283', 'f7', '176', 'd0', '2ba', '1bc', '9c', '278', '25f', '23e', '260', '1da', '28e', 'e7', 'ad', '195', '2a3', '148', '1aa', '151', '18b', '105', '225', '110', '2bb', '223', '1ed', '2fe', '184', '131', '191', '2b6', '150', '80', '55', '2aa', '68', '11d', '20e', '249', '294', '219', '21e', '1eb', '207', '12f', 'd6', '193', '171', 'da', '6e', '12b', '2ea', 'bb', 'a1', '21f', '17e', '27f', '23c', '21c', '17b', '280', '1ee', 'e2', '117', '6c', '1c5', 'e6', '5d', '161', '162', '1e7', '331', 'f2', '221', '1f3', '1c3', '142', '2ce', '1a0', '1bf', '1f5', '13a', 'f8', '262', '305', '203', '12e', '275', '25c', '111', 'e8', '9a', 'c4', '4e', '22e', '50', '2c2', '205', '297', '1ff', '126', '182', '1c0', '10c', '185', '271', '235', '2d2', '92', '123', '1d5', '81', '302', '10b', '261', '181', '1a5', '2f0', '2d8', '2a1', 'd2', '1c8', '1c2', 'ef', '109', '29c', '1af', '226', 'ca', '158', '99', 'bf', '18d', '217', 'd7', 'c6', 'cc', 'c5'] 255
'''

