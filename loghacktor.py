#!/usr/bin/python2.6

"""
Anonymize the IP address in hack_tor output.
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

	while True:
		line = sys.stdin.readline()
		if line == "":
			exit()

		flush_count += 1

		split = line.split(" ")
		split[6] = str(ip_map[split[6]])
		print " ".join(split)

		if flush_count > 1024:
			sys.stdout.flush()
			flush_count = 0
