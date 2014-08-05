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


"""

from datetime import datetime
from pprint import pprint
import sys, re

'''
	Pseudonymizes the ip addresses.
	@param line: a line from scallion.log
	@param ip_dict: a dictionary of the form {real_ip_address: pseudo_ip_address}
	@param ip_pseudo: the integer representing the pseudonymized ip address
	@return the line with the replaced ip_addr split into list format,
			the dictionary of the form {real_ip_address: pseudo_ip_address},
			and the integer representing the pseudonymized ip address
'''
def ip_replace(line, ip_dict, ip_pseudo):
	split = line.split()

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
	nodename = sys.argv[2]  # nodename = name of relay/node wanted --
                            # in the example above, this is 2.relay
	outfile = sys.argv[3]

#	f_name = "tor_fmt_" + nodename + ".log"
	ip_dict = {}
	ip_pseudo = 1

	with open(infile, "r") as f_in, open(outfile, "w") as f_out:
		print "Reading file..."
		n_entries = 0
		print "Converting to tor format..."
		for line in f_in:
#		while True:
#			line = sys.stdin.readline() # read in a log line from stdin from the shadow log
#			if line == "":
#				exit()
			n_entries += 1
			if n_entries % 50000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries


			if ("CLIENTLOGGING" in line):
				# pseudonomyize ip addresses
				split, ip_dict, ip_pseudo = ip_replace(line, ip_dict, ip_pseudo)

				name = split[4].split("-")[0].replace("[", "") # get the name of relay/node without the IP addr
				if (name == nodename):

					# get virtual time
					hours, minutes, seconds, nano = [int(x) for x in split[2].split(":")]
					loglevel = "[notice]"
					date = datetime(2013, 1, 1, hours, minutes, seconds, nano/1000)
					date_fmt = date.strftime("%b %d %H:%M:%S.%f")[0:-3]
					tor_log = date_fmt + " " + loglevel + " " + " ".join(split[6:]) + "\n"
					f_out.write(tor_log)
	
	print "Done\n"
	# save pseudo ip map
	#with open("pseudo_dict_scallion50.log","w") as dict_out:
	#	dict_out.write(str(ip_dict))

