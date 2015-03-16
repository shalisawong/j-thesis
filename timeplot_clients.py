'''
Pre-processing for plotting multiple time series data for specific clients. 

@author Shalisa Pattarawuttiwong
Last Edited: 08/05/2014
'''

import sys, re, cPickle, random

'''
	Extracts the host name and ip addresses from scallion.log and 
	returns a dictionary of {client_name: [circ_id1, circ_id2, ...]}. 
	Checks only valid circuits.
	@param infile: a scallion.log file
	@param ident_list: a list of the identifiers of the series, 
		in the format [('circ_id,ip_slug')]
	@return: a dictionary of {client_name: [circ_id1, circ_id2,...]}. 
'''
def circuit_client_map(infile, ident_list):

	ip_addresses = {}
	circuits = {}
	circ_name_map = {}
	valid_circs = [hex(i[0])[2:] for i in ident_list]

	with open(infile) as f:
		print "Reading file..."
		n_entries = 0
		print "Mapping Clients and Circuits..."
		for line in f:
			n_entries += 1
			if n_entries % 50000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries

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
			if "CLIENTLOGGING" in line:
			#if nodename and "CLIENTLOGGING" in line:
				split = line.split()
				circ_id = split[-1]
				prev_ip = split[8]

				if circ_id in valid_circs and circ_id not in circuits:
						circuits[circ_id] = prev_ip
				
		for circ in circuits:
				name = ip_addresses[circuits.get(circ)]

				if name not in circ_name_map:
					circ_name_map[name] = [int(circ, 16)]
				elif name in circ_name_map:
					circ_list = circ_name_map.get(name)
					circ_list.append(int(circ, 16))
		
	return circ_name_map # dict of {clientname:[circ1,circ2,circ3]}

'''
	@param parsed_pickle_file: name of a parsed, windowed, 
		and trimmed pickle file
	@return: the list of idents from a parsed, windowed, 
		and trimmed window pickle file (_trimmed_good.pickle)
'''
def get_ident_list(parsed_pickle_file):
	with open(parsed_pickle_file, 'r') as ident_log:
			data = cPickle.load(ident_log)
			records = data['records']
			ident_list = []
			for record in records:
					ident = record['ident']
					ident_list.append(ident)
			return ident_list

'''
	Logs circ_name_map and ident_list into "client_info.log"
	@param circ_name_map: a dictionary of 
		{client_name: [circ_id1, circ_id2,...]}.
	@param ident_list: a list of idents from a parsed, windowed, 
		and trimmed window pickle file (_trimmed_good.pickle) in the 
		form [(circ_id,ip_slug)].


'''
def write_client_info_log(circ_name_map, ident_list):
		with open("client_info.log", 'w') as client_log:
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

			client_log.write(str(ident_list))
	
'''
	Returns a ts_ident string to input into exploratory.py
	@param circ_name_map: a dictionary of 
		{client_name: [circ_id1, circ_id2,...]}.
	@param ident_list: a list of idents from a parsed, windowed, 
		and trimmed window pickle file (_trimmed_good.pickle) in the form
		[(circ_id,ip_slug)]
	@param type_client: a string of the client wanted 
		(web, bulk, perfclient50k, perfclient1m, perclient5m, -allClients)
	@param num_graphs: an integer of the number of timeplots wanted
	@return: a string of ts_idents in the correct format for exploratory.py
 		in the form "'circ_id1,ip_slug1' 'circ_id2,ip_slug2' 'circ_id3,ip_slug3' ..." 
'''
def input_timeplot_single_client(circ_name_map, ident_list, type_client, num_graphs):
	filt_circ_name_map = {k:v for (k,v) in circ_name_map.iteritems() if type_client in k}
	totalcircs = sum(len(v) for v in filt_circ_name_map.itervalues())
	print filt_circ_name_map, totalcircs
	ident_string = ''
	repeat = []

	while num_graphs > 0:
		# pick client and specific circuit.. may have issues if num_graphs > num_totalcircs
		client = random.choice(filt_circ_name_map.keys())
		circ = random.choice(circ_name_map.get(client))
		# grab ident
		for item in ident_list:
			if (item[0] == circ and item not in repeat):
				repeat.append(item)
				ident = "'" + str(item[0]) + "," + str(item[1]) + "' "
				ident_string += ident
				num_graphs -= 1
			# may have issues if num_graphs => num_totalcircs, if so, allow repeation
			elif (len(repeat) == totalcircs):
				ident = "'" + str(item[0]) + "," + str(item[1]) + "' "
				ident_string += ident
				num_graphs -= 1
	return ident_string

'''
	If type_client is -allClients, return a dictionary of {client_type: ident_string}
	else return the ident_string
	@param circ_name_map: a dictionary of 
		{client_name: [circ_id1, circ_id2,...]}.
	@param ident_list: a list of idents from a parsed, windowed, 
		and trimmed window pickle file (_trimmed_good.pickle) in the form
		[(circ_id,ip_slug)]
	@param type_client: a string of the client wanted 
		(web, bulk, perfclient50k, perfclient1m, perclient5m, -allClients)
	@param num_graphs: an integer of the number of timeplots wanted

'''
def input_timeplot_clients(circ_name_map, ident_list, type_client, num_graphs):
	ident_string_dict = {}
	if type_client == "-allClients":
		web = input_timeplot_single_client(circ_name_map, ident_list,
											'web', num_graphs)
		ident_string_dict['web'] = web
		print web
		bulk = input_timeplot_single_client(circ_name_map, ident_list,
											'bulk', num_graphs)
		ident_string_dict['bulk'] = bulk
		print bulk
		perf50k = input_timeplot_single_client(circ_name_map, ident_list, 
											'perfclient50', num_graphs)
		ident_string_dict['perf50k'] = perf50k
		print perf50k
		perf1m = input_timeplot_single_client(circ_name_map, ident_list, 
											'perfclient1m', num_graphs)
		ident_string_dict['perf1m'] = perf1m
		print perf1m
		perf5m = input_timeplot_single_client(circ_name_map, ident_list, 
											'perfclient5m', num_graphs)
		ident_string_dict['perf5m'] = perf5m
		print perf5m
		return ident_string_dict
	else:
		return input_timeplot_single_client(circ_name_map, ident_list,
											type_client, num_graphs)


if __name__ == "__main__":
	infile = sys.argv[1]
	parsed_pickle = sys.argv[2]
	#nodename = sys.argv[3]
	type_client = sys.argv[4]
	num_graphs = int(sys.argv[5])

	ident_list = get_ident_list(parsed_pickle)
	circ_name_map = circuit_client_map(infile, ident_list) 

	print input_timeplot_clients(circ_name_map, ident_list, type_client, num_graphs)


