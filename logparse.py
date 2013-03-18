"""
Parse a hack_tor log file, and output the resulting records in JSON.
Syntax: python logparse.py infile outfile direction
Direction is either "O" for outgoing cells, or "I" for incoming cells.
The logfile this outputs is in the format:
[ { 'ident': [circuit id, ip slug]
	'create': timestamp of last create cell received
	'relays': list of timestamps for all relay cells in the circuit
	'destroy': timestamp of last destroy cell received
  },
  { ... },
  { ... },
  ...
]
"""

from datetime import datetime
import sys, json

def parse_time(time_str):
	"""
	Parse a time string from the Tor logfile. Returns the number of milliseconds
	since January 1, 2013. We use this date instead of the epoch to avoid enormous
	timestamps.

	@param time_str: The time string from the logfile
	@return: The number of milliseconds since January 1, 2013
	"""
    augmented = '2013 ' + time_str
    date_parsed = datetime.strptime(augmented[0:-4],'%Y %b %d %H:%M:%S')
    n_seconds = 1.0*(date_parsed - datetime(2013, 1, 1)).total_seconds()
    n_milliseconds = int(time_str[-3:])
    print date_parsed
    return 1000*n_seconds + n_milliseconds

def parse_line(line):
	"""
	Parse the circuit id, ip slug, and timestamp from a line in
	the hack_tor log file.
	@param line: The line
	@return: A dictionary {
		'ident': (circid, ipslug),
		'time': the timestamp
	}
	"""
	split = line.split(" ")
	circid = int(split[5])
	ipslug = int(split[6])
	time = parse_time(line[0:19])
	return {
		'ident': (circid, ipslug),
		'time': time
	}

if __name__ == "__main__":
	lfpath = sys.argv[1]
	outpath = sys.argv[2]
	direc = sys.argv[3].upper()
	with open(lfpath) as logfile:
		print "Reading file..."
		create_times = {} # map circuit idents to start times
		time_series = {} # map circuit idents to time series
		zero_circ_ids = []
		n_incomplete = 0
		print "Parsing..."
		# First pass - determine which circuits are complete
		for line in logfile:
			if line[29:35] == "CREATE":
				record = parse_line(line)
				ident = record['ident']
				create_time = record['time']
				create_times[ident] = create_time
			elif line[29:36] == "DESTROY":
				record = parse_line(line)
				ident = record['ident']
				create_time = create_times.get(ident)
				if create_time is not None:
					destroy_time = record['time']
					# This can actually happen, believe it or not. Likely explanation
					# is that the CREATE cell suffered more latency than the DESTROY,
					# so they both arrived at the same time.
					time_series[ident] = {
						'ident': ident
						'create': create_time,
						'relays': [],
						'destroy': destroy_time,
					}
		logfile.seek(0)
		# Second pass - build time series for complete circuits
		print "Adding relay timing data..."
		for line in logfile:
			if line[29:33] == "RRC" + direc:
				record = parse_line(line)
				series = time_series.get(record['ident'])
				if series is not None:
					series['relays'].append(record['time'])
		n_incomplete = len(create_times) - len(time_series)
		# Third pass - remove invalid circuits. It takes at least 4 relay cells
		# to build a valid circuit, so we ignore anything less.
		print "Removing circuits with too few relay cells"
		for ident, record in time_series.iteritems():
			if len(record['relays']) < 4:
				zero_circ_ids.append(ident)
		for ident in zero_circ_ids:
			del time_series[ident]
		percent_complete = 100 * 1.0*len(time_series)/len(create_times)
		print "** There were %i circuits total" % len(create_times)
		print "** %i circuits only had CREATE cells" % n_incomplete
		print "** %i circuits had CREATE and DESTROY, but no RELAY" % len(zero_circ_ids)
		print "** %d%% (%i) valid, complete circuits" % (percent_complete,
			len(time_series))
		with open(outpath, 'w') as outfile:
			print "Dumping data to %s" % outpath
			json.dump(time_series.values(), outfile)
