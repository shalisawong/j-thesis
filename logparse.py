"""
Parse a hack_tor log file infile and output the resulting records as a
pickled list.

	Syntax: python2.7 logparse.py infile outfile

The output file is a pickled list in the format:
[ { 'ident': [circuit id, ip slug]
	'create': timestamp of last create cell received
	'destroy': timestamp of last destroy cell received
	'relays_in': list of timestamps for incoming relay cells
	'relays_out': list of timestamps for outgoing relay cells
  },
  { ... },
  { ... },
  ...
]
@author: Julian Applebaum

****Edited 7/16/15 with clientlogging modifications**** @author: Shalisa Pattarawuttiwong


"""

from pprint import pprint

from datetime import datetime
import sys, cPickle

def parse_time(time_str):
	"""
	Parse a time string from the hack_tor logfile. Returns the number
	of milliseconds since January 1, 2013. We use this date instead of
	the epoch to avoid enormous timestamps.

	@param time_str: The time string from the logfile
	@return: The number of milliseconds since January 1, 2013
	"""
	augmented = "2013 " + time_str
	date_parsed = datetime.strptime(augmented[0:-4],'%Y %b %d %H:%M:%S')
	n_seconds = 1.0*(date_parsed - datetime(2013, 1, 1)).total_seconds()
	n_milliseconds = int(time_str[-3:])
	return 1000*n_seconds + n_milliseconds

def parse_line(line="Jan 01 00:20:01.260 [notice] CLIENTLOGGING: 11.0.0.3 <- 11.0.0.9 (2147484638 <- 10637) CIRC 18"):
	"""
	Parse the circuit id, ip slug, and timestamp from a line in
	the hack_tor log file.
	@param line: The line
	@return: A tuple ((circid, ipslug), timestamp)
	"""
        # hex vs int????
	split = line.split(" ")
	circid = int(split[-1], 16)
	ipslug = int(split[6], 16)                    # should be pseudonymized and be an int
	time = parse_time(line[0:19])
	return ((circid, ipslug), time)

def is_valid_circ(record):
	"""
	Used for filtering out invalid circuits, which could occur given
	a misbehaving Tor client. To construct a 3-hop circuit, the client
	needs to send at least 3 RELAY cells, and at least 3 acknowledging
	RELAY cells need to be sent back. The circuit must also be terminated
	with at least one DESTROY cell. All RELAY cells must be sent between
	the last CREATE cell and the first DESTROY cell.
	@param record: the record representing a circuit
	@return: True if the circuit is valid, false otherwise
	"""
	return (record['destroy'] is not None and
		    len(record['relays_in']) >= 3 and
			len(record['relays_out']) >= 3 and
			record['relays_out'][0] >= record['create'] and
			record['relays_out'][-1] <= record['destroy'] and
			record['relays_in'][0] >= record['create'] and
			record['relays_in'][-1] <= record['destroy'])

if __name__ == "__main__":
	lfpath = sys.argv[1]     # the tor formatted log file -- tor_fmt_relayname.log
	outpath = sys.argv[2]
	with open(lfpath) as logfile:
		print "Reading file..."
		records = {}
		n_entries = 0
		print "Parsing..."
		for line in logfile:
			n_entries += 1
			if n_entries % 50000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries

			if line[44:51] == "CREATED":
				# In the case of multiple CREATE cells, we define the
				# beginning of the circuit as the time at which the last
				# CREATE was sent.
				ident, time = parse_line(line)
				records[ident] = {
					'ident': ident,
					'create': time,
					'destroy': None,
					'relays_in': [],
					'relays_out': []
				}
			elif line[44:51] == "DESTROY":
				ident, time = parse_line(line)
				record = records.get(ident)
				if record is not None:
					# In the case of multiple DESTROY cells, we define the
					# end of the circuit as the time at which the first
					# DESTROY was sent.
					if record['destroy'] is None:
						record['destroy'] = time

			elif line[44:49] == "RELAY":  # changed from RRC to RELAY
				ident, time = parse_line(line)
				record = records.get(ident)
				direc = line[53:55]
				if record is not None:
					if direc == "<-":
						record['relays_in'].append(time)
					elif direc == "->":
						record['relays_out'].append(time)

		with open(outpath, 'w') as outfile:
			print "Removing invalid circuits..."
			filtered = filter(is_valid_circ, records.itervalues())
			print "%i circuits total" % len(records)
			print "%i (%.2f%%) valid circuits" % (len(filtered),
				100.0*len(filtered)/len(records))
			print "Dumping valid circuits to %s" % outpath

			cPickle.dump(filtered, outfile, protocol=2)


