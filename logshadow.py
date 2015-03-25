#!/usr/bin/python2.7

"""
Filter and modify Scallion log output to look like regular Tor output.
Takes 1 argument, the name of the node whose log we want. Properly
formatted dates are created from virtual timestamps. Log output is taken from stdin.

An example line of output from scallion.log:

0:0:3:992256 [thread-0] 0:0:5:000000000 [scallion-message] [2.relay-76.1.0.0] [intercept_logv] [notice] command_process_create_cell() CREATE: 53683 63.1.0.0

Output (regular Tor output):
Jan 01 00:00:05.000 [notice] CREATE: 53683 63.1.0.0

****Edited 7/16/15 with clientlogging modifications**** 7/24/14
@author Shalisa Pattarawuttiwong

example input at [notice] log level taken from filtered_scallion.log output:
00:19:09:350102143 [relay2-11.0.0.6] CLIENTLOGGING: RELAY 11.0.0.3 -> 11.0.0.9 CIRC 18
(hour:minute:second:nanosecond)

output:
Jan 01 00:19:09.350 [notice] CLIENTLOGGING: RELAY 1 -> 2 CIRC 18
(hour:minute:second:mircosecond)

syntax: python logshadow.py infile nodename outfile

****Edited 3/2/15 ****
@author Shalisa Pattarawuttiwong
Since tor itself pseudonymizes ip addresses, don't need ip_replace

"""

from datetime import datetime
from pprint import pprint
import sys, re, cPickle

'''
	Pseudonymizes the ip addresses.
	@param line: a line from scallion.log
	@param ip_dict: a dictionary of the form {real_ip_address: pseudo_ip_address}
	@param ip_pseudo: the integer representing the pseudonymized ip address
	@return the line with the replaced ip_addr split into list format,
			the dictionary of the form {real_ip_address: pseudo_ip_address},
			and the integer representing the pseudonymized ip address
'''
def ip_replace(split, ip_dict, ip_pseudo):
	# split = line.split()
	relay_ip = split[4].split("~")[0].replace("[", "")
	#if (relay_ip in ip_dict):
	#	new_relay_ip = ip_dict.get(relay_ip)
	#else:
	#	hex_relay_ip = hex(ip_pseudo)[2:]
	#	ip_dict[relay_ip] = hex_relay_ip
	#	new_relay_ip = hex_relay_ip
	#	ip_pseudo += 1
	#split[4] = str(new_relay_ip)
	split[4] = relay_ip

	# grab ip addresses
	p_relay = split[8]
	if split[7] != "CREATE":
		n_relay = split[10]
	else:
		# no n_relay
		n_relay = 0

	# p_relay
	if (p_relay in ip_dict):
		new_p_relay = ip_dict.get(p_relay)
	else:
		hex_ip = hex(ip_pseudo)[2:]
		ip_dict[p_relay] = hex_ip
		new_p_relay = hex_ip
		ip_pseudo += 1

	split[8] = str(new_p_relay)

	# n_relay
	if (n_relay != 0):
		if (n_relay in ip_dict):
			new_n_relay = ip_dict.get(n_relay)
		else:
			hex_ip = hex(ip_pseudo)[2:]
			ip_dict[n_relay] = hex_ip
			new_n_relay = hex_ip
			ip_pseudo += 1

		split[10] = str(new_n_relay)
	return split, ip_dict, ip_pseudo


if (__name__ == "__main__"):
	infile = sys.argv[1]
	#nodename = sys.argv[2]  # nodename = name of relay/node wanted --
                            # in the example above, this is 2.relay
	outfile = sys.argv[2]
	outpickle = infile[:-4] + "_pseudo_ip.pickle"

	ip_dict = {}
	ip_pseudo = 1
	num_cl = 0
	unique_sc = 0
	sc = 0
	trans_comp = 0
	built = 0
	sc_dict = []

# ./data/relays-50r-180c.csv
	with open(infile, "r") as f_in, open(outfile, "w") as f_out:
		print "Reading file..."
		n_entries = 0
		print "Converting to tor format..."
		for line in f_in:
			n_entries += 1
			if n_entries % 50000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries

			split = line.split()
			if "BUILT" in line:
				built = built + 1

			if "GET" in line and "transfer-complete" in line:
				trans_comp = trans_comp + 1

			if "SENTCONNECT" in line and split[-1].split(":")[1] == "80":
				sc = sc + 1
				if [split[12],split[4]] not in sc_dict:
					sc_dict.append([split[12],split[4]])
					unique_sc = unique_sc + 1
		
			# previous relay is a client
			if (split[6] == "CLIENTLOGGING:" and split[8].startswith("11.0.")):
				num_cl = num_cl + 1
				# pseudonomyize ip addresses
				split, ip_dict, ip_pseudo = ip_replace(split, ip_dict, ip_pseudo)
				ip = split[4]
				# get virtual time
				hours, minutes, seconds, nano = [int(x) for x in split[2].replace(".",":").split(":")]
				loglevel = "[notice]"
				date = datetime(2013, 1, 1, hours, minutes, seconds, nano/1000)
				date_fmt = date.strftime("%b %d %H:%M:%S.%f")[0:-3]
				tor_log = date_fmt + " " + loglevel + " " + ip + " " + " ".join(split[6:]) + "\n"
				f_out.write(tor_log)

	print "\ntotal SENTCONNECT: " + str(sc)
	print "unique SENTCONNECT: " + str(unique_sc)
	print "total GET: " + str(trans_comp)
	print "total BUILT: " + str(built)
	print "Filtered cell count: " + str(num_cl)
	# save pseudo ip map
	with open(outpickle, "w") as outfile:
		ip_dict_flip = {v:k for k, v in ip_dict.items()}
		cPickle.dump(ip_dict_flip, outfile, protocol=2)
 		print "Dumping ip address dictionary to %s" % outpickle
	print "Done\n"

