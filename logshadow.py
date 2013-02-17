#!/usr/bin/python2.6

"""
Filter and modify Scallion log output to look like regular Tor output.
Takes 1 argument, the name of the node whose log we want. Properly
formatted dates are created from virtual timestamps. Log output is taken from stdin.

An example line of output from scallion.log:

0:0:3:992256 [thread-0] 0:0:5:000000000 [scallion-message] [2.relay-76.1.0.0] [intercept_logv] [notice] command_process_create_cell() CREATE: 53683 63.1.0.0
"""

from datetime import datetime
from pprint import pprint
import sys, re

if __name__ == "__main__":
	nodename = sys.argv[1]

	while True:
		line = sys.stdin.readline()
		if line == "":
			exit()

		split = line.split()

		if split[5] == "[intercept_logv]":
			name = split[4].split("-")[0].replace("[", "")

			if name == nodename:
				hours, minutes, seconds, nano = [int(x) for x in split[2].split(":")]
				loglevel = split[6]
				date = datetime(2013, 1, 1, hours, minutes, seconds, 1000*nano)
				date_fmt = date.strftime("%b %d %H:%M:%S.%f")[0:-3]
				print date_fmt, loglevel, " ".join(split[8:])
