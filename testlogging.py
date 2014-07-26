#import autotor
import sys

"""
Compare a raw Tor log to the corresponding one produced by loghacktor.py.
Verify that all timing info is the same, circuit ids are identical, and
anonymized ip addresses have been mapped in a consistent manner.
"""

def Julian_compare():

		log_orig = autotor.MultiLogFile(sys.argv[1])
		log_ht = autotor.MultiLogFile(sys.argv[2])

		assert len(log_orig.circs) == len(log_ht.circs)
		ip_map = {}

		# For each circuit, first check that everything aside from the IP addresses
		# is identical. Then, check that the anonymized IP addresses remain consistent.
		for k in log_orig.circs.keys():
			assert k in log_orig.circs
			assert k in log_ht.circs
			e5circ, e5htcirc = log_orig.circs[k], log_ht.circs[k]
			assert e5circ['times'] == e5htcirc['times']
			assert e5circ['src_circ'] == e5htcirc['src_circ']
			assert e5circ['src_circ'] == e5htcirc['src_circ']

			orig_src, orig_dst = e5circ['src_addr'], e5circ['dst_addr']

			if orig_src not in ip_map:
				ip_map[orig_src] = e5htcirc['src_addr']
			else:
				assert ip_map[orig_src] == e5htcirc['src_addr']

			if orig_dst not in ip_map:
				ip_map[orig_dst] = e5htcirc['dst_addr']
			else:
				assert ip_map[orig_dst] == e5htcirc['dst_addr']


		# cell rate: 152981 cells/second
		# data rate: 74399 KB/s
		# total time: 8 seconds

'''
	Compare a raw Tor log to the corresponding one produced by logshadow.py.
	Verify that all timing info is the same, circuit ids are identical, and
	pseudoanonymized ip addresses have been mapped in a consistent manner.

'''
from itertools import izip

def compare_logging():

	log_orig = sys.argv[1]
	log_pseudo = sys.argv[2]

	ip_dict = {'46.4.87.172': '6', '11.0.0.6': '1c', '11.0.0.8': '1a', '11.0.0.2': '20', '11.0.0.3': '1f', '11.0.0.4': '1e', '11.0.0.5': '1d', '38.229.0.29': '4', '11.0.0.7': '1b', '94.198.98.155': '2', '11.0.0.9': '19', '46.14.245.206': 'd', '67.243.19.7': 'f', '24.211.140.67': 'c', '167.88.35.223': 'a', '11.0.0.13': '15', '11.0.0.10': '18', '77.183.246.223': 'e', '11.0.0.16': '12', '11.0.0.14': '14', '11.0.0.15': '13', '66.231.133.113': '9', '81.150.197.174': '10', '69.164.196.238': '7', '11.0.0.11': '17', '213.112.74.156': '8', '130.255.73.202': '1', '151.15.33.145': '11', '11.0.0.1': '21', '209.148.46.129': '3', '188.226.171.111': 'b', '95.85.11.116': '5', '11.0.0.12': '16'}


	ip_map = {}

	with open(log_orig, "r") as orig, open(log_pseudo, "r") as pseudo:
		for line_o, line_p in izip(orig, pseudo):	
			split_o = line_o.split()
			split_p = line_p.split()
			assert len(split_o) == len(split_p)	
	
			for i in range(len(split_o)):
					# checking if all but ip addresses are identical
					if ((i != 6 and i != 8 and split_o[5] != "CREATE" and split_p[5] != "CREATE") or 
						(i != 6 and split_o[5] == "CREATE" and split_p[5])):
						assert split_o[i] == split_p[i]
					elif (i == 6 or (i == 8 and split_o[5] != "CREATE")):
						 if split_o[i] not in ip_map:
							ip_map[split_o[i]] = split_p[i]
						 else:
							assert ip_map[split_o[i]] == split_p[i]

	for key in ip_map:
		if key not in ip_dict.keys():
			print key, "not in ip_dict as a key"
		if ip_map.get(key) not in ip_dict.values():
			print value, "not in ip_dict as a value"

	print ip_map
	print cmp(ip_dict,ip_map)
#	assert cmp(ip_dict, ip_map) == 0

compare_logging()

'''
ip_dict
{'46.4.87.172': '6', '11.0.0.6': '1c', '11.0.0.8': '1a', '11.0.0.2': '20', '11.0.0.3': '1f', '11.0.0.4': '1e', '11.0.0.5': '1d', '38.229.0.29': '4', '11.0.0.7': '1b', '94.198.98.155': '2', '11.0.0.9': '19', '46.14.245.206': 'd', '67.243.19.7': 'f', '24.211.140.67': 'c', '167.88.35.223': 'a', '11.0.0.13': '15', '11.0.0.10': '18', '77.183.246.223': 'e', '11.0.0.16': '12', '11.0.0.14': '14', '11.0.0.15': '13', '66.231.133.113': '9', '81.150.197.174': '10', '69.164.196.238': '7', '11.0.0.11': '17', '213.112.74.156': '8', '130.255.73.202': '1', '151.15.33.145': '11', '11.0.0.1': '21', '209.148.46.129': '3', '188.226.171.111': 'b', '95.85.11.116': '5', '11.0.0.12': '16'}

ip_map 
{'46.4.87.172': '6', '11.0.0.1': '21', '11.0.0.2': '20', '11.0.0.3': '1f', '11.0.0.6': '1c', '11.0.0.7': '1b', '94.198.98.155': '2', '11.0.0.9': '19', '46.14.245.206': 'd', '67.243.19.7': 'f', '24.211.140.67': 'c', '167.88.35.223': 'a', '11.0.0.13': '15', '11.0.0.10': '18', '11.0.0.11': '17', '11.0.0.16': '12', '11.0.0.14': '14', '11.0.0.15': '13', '66.231.133.113': '9', '81.150.197.174': '10', '69.164.196.238': '7', '213.112.74.156': '8', '130.255.73.202': '1', '151.15.33.145': '11', '209.148.46.129': '3', '95.85.11.116': '5', '11.0.0.12': '16'}

'''


