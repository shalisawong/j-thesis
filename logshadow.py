#!/usr/bin/python2.6

"""
Filter and modify Scallion log output to look like regular Tor output.
Takes 1 argument, the name of the node whose log we want. Properly
formatted dates are created from virtual timestamps. Log output is taken from stdin.

An example line of output from scallion.log:

0:0:3:992256 [thread-0] 0:0:5:000000000 [scallion-message] [2.relay-76.1.0.0] [intercept_logv] [notice] command_process_create_cell() CREATE: 53683 63.1.0.0

Output (regular Tor output):
Jan 01 00:00:05.000 [notice] CREATE: 53683 63.1.0.0

****Edited 7/16/15 with clientlogging modifications****

example input at [notice] log level taken from filtered_scallion.log output:
00:19:09:350102143 [relay2-11.0.0.6] CLIENTLOGGING: 11.0.0.3 -> 11.0.0.9 (2147484638 -> 10637) CIRC 18
(hour:minute:second:nanosecond)

output:
Jan 01 00:19:09.350 [notice] CLIENTLOGGING: 11.0.0.3 -> 11.0.0.9 (2147484638 -> 10637) CIRC 18
(hour:minute:second:mircosecond)
"""

from datetime import datetime
from pprint import pprint
import sys, re

if __name__ == "__main__":
	nodename = sys.argv[1]  # nodename = name of relay/node wanted -- 
                            # in the example above, this is 2.relay
	
	f_name = "tor_fmt_" + nodename + ".log"
	with open(f_name, "w") as f_out:
	
		while True:
			line = sys.stdin.readline() # read in a log line from stdin from the shadow log
			if line == "":
				exit()

			split = line.split() # split the log
			if "CLIENTLOGGING" in line: 
				name = split[1].split("-")[0].replace("[", "") # get the name of relay/node without the IP addr
				# get virtual time
				if name == nodename:
					hours, minutes, seconds, nano = [int(x) for x in split[0].split(":")]
					loglevel = "[notice]"
					date = datetime(2013, 1, 1, hours, minutes, seconds, nano/1000)
					date_fmt = date.strftime("%b %d %H:%M:%S.%f")[0:-3]
					tor_log = date_fmt + " " + loglevel + " " + " ".join(split[2:]) + "\n"
					f_out.write(tor_log)
