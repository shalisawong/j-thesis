#!/usr/bin/python2.6

"""
Filter and modify Scallion log output to look like regular Tor output.
Takes 1 argument, the name of the node whose log we want. Properly
formatted dates are created from virtual timestamps. Log output is taken from stdin.

NOTE: We're assuming a modified version of Scallion in which the log level indicator
is made consistent with that of unmodified Tor.
"""

from datetime import datetime
import sys, re

name_re = re.compile(".+([0-9]+:[0-9]+:[0-9]+:[0-9]+) \[scallion-message\] " +
					 "\[([a-zA-Z0-9]+)-[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\].+")
nodename = sys.argv[1]

while True:
	line = sys.stdin.readline()
	if line == "": exit()

	re_match = name_re.search(line)
	if re_match and re_match.group(2) == nodename:
		hours, minutes, seconds, nano = [int(x) for x in re_match.group(1).split(":")]
		date = datetime(2012, 11, 1, hours, minutes, seconds, 1000*nano)
		date_fmt = date.strftime("%b %d %H:%M:%S.%f")[0:-3]
		split = line[line.find("[intercept_logv]") + 17:-1].split(" ")
		del split[1]
		print date_fmt, " ".join(split)
