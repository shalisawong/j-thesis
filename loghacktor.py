#!/usr/bin/python2.6

"""
Anonymize the IP address in hack_tor output.  Invocation syntax:

loghacktor.py <ctrl_port_pw> <output_file>

"""

import getpass
import sys

from stem.control import Controller


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

	# Process command-line arguments.
	passwd, output_filename = sys.argv[1:]
	# passwd = getpass.getpass("Control port p/w: ")

	# Get the list of IPs for known relays.
	known_relays = set()
	with Controller.from_port(control_port = 9051) as controller:
		controller.authenticate(password=passwd)

		for desc in controller.get_server_descriptors():
			known_relays.add(desc.address)

	# Process each line from standard input, which should be just
	# the messages in the HACKTOR logging domain.  Extract the IP
	# address from each line.  If the IP address does not belong to
	# a known relay, anonymize it and write the anonymized version
	# of the message to standard out.
	with open(output_filename, 'w') as output_file:
		flush_count = 0
		while True:
			line = sys.stdin.readline()
			if line == "":
				output_file.close()
				exit()

			flush_count += 1

			split = line.split()
			if split[6] in known_relays: continue

			split[6] = str(ip_map[split[6]])
			output_file.write(" ".join(split) + "\n")

			if flush_count > 1024:
				output_file.flush()
				flush_count = 0
