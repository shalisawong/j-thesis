#!/usr/bin/python2.6

"""
Filter Tor log output. hack_tor statements are directed to a user-specified file,
while everything else is echoed to stdout. IP addresses in hack_tor statements are
anonymized. Takes 1 argument - the path of the file to write hack_tor output to.
"""

import sys

class SlugMap(dict):
	"""
	A dict that generates new anonymized slugs when a mapping isn't present.
	"""
	def __init__(self, *args, **kwargs):
		super(dict, self).__init__(*args, **kwargs)
		self.slug = 0

	def __missing__(self, key):
		slug = self.slug
		self.slug += 1
		self[key] = slug
		return slug

ip_map = SlugMap()

if __name__ == "__main__":
	flush_count = 0

	with open(sys.argv[1], 'w') as logfile:
		while True:
			line = sys.stdin.readline()
			flush_count += 1

			if line[29:32] == "RRC":
				split = line.split(" ")
				n_addr = split[5]
				p_addr = split[7]
				n_addr2 = ip_map[n_addr]
				p_addr2 = ip_map[p_addr]
				split[5] = str(n_addr2)
				split[7] = str(p_addr2)
				logfile.write(" ".join(split))
			else:
				print line,

			if flush_count > 1024:
				sys.stdout.flush()
				logfile.flush()
				flush_count = 0
