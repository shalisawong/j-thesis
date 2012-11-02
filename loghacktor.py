#!/usr/bin/python2.6

"""
Filter Tor log output. hack_tor statements are directed to user-specified file,
while everything else is pushed to stdout. IP addresses in hack_tor statements
are anonymized. Takes 1 argument - the path of the file to write hack_tor output
to.
"""

import sys, re

def b8(n, i):
	"""
	Get the ith 8 bit integer, starting from bit 0, of n
	"""
	n8 = 0

	for j in xrange(0, i+1):
		for k in xrange(0, 8):
			if j == i: n8 += 2**k * (n % 2)
			n /= 2

	return n8

class Ipv4Generator(object):
	"""
	Generate ascending IPv4 addresses.
	"""
	def __init__(self):
		self.addr = 0

	def __call__(self):
		addr_str = "%i.%i.%i.%i" % ( b8(self.addr, 3), b8(self.addr, 2),
									 b8(self.addr, 1), b8(self.addr, 0) )
		self.addr += 1
		return addr_str

next_addr = Ipv4Generator()
ip_map = {}
ip_re = re.compile("([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})")

if __name__ == "main":
	with open(sys.argv[1], 'w') as logfile:
		while True:
			line = sys.stdin.readline()
			if line == "": exit()

			if line.find("RRC") != -1:
				n_addr_match = ip_re.search(line)
				n_addr = n_addr_match.group(1)

				p_addr_match = ip_re.search(line[n_addr_match.end(1):-1])
				p_addr = p_addr_match.group(1)

				n_addr2 = ip_map.get(n_addr) or next_addr()
				p_addr2 = ip_map.get(p_addr) or next_addr()

				ip_map[n_addr] = n_addr2
				ip_map[p_addr] = p_addr2
				line = line.replace(n_addr, n_addr2).replace(p_addr, p_addr2)
				logfile.write(line)
			else:
				print line,
