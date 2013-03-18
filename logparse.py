"""
Parse a hack_tor log file infile and output the resulting records as JSON
to outfile.
	Syntax: python2.7 logparse.py infile outfile direction
Direction is either "O" for outgoing cells, or "I" for incoming cells.
The output file is a JSON string in the format:
[ { 'ident': [circuit id, ip slug]
	'create': timestamp of last create cell received
	'relays': list of timestamps for all relay cells in the circuit
	'destroy': timestamp of last destroy cell received
  },
  { ... },
  { ... },
  ...
]
@author: Julian Applebaum
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
		records = {}
		n_entries = 0
		bad_circ_idents = set()
		print "Parsing..."
		for line in logfile:
			n_entries += 1
			if n_entries % 10000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries
			if line[29:35] == "CREATE":
				entry = parse_line(line)
				ident = entry['ident']
				create_time = entry['time']
				records[ident] = {
					'ident': ident,
					'create': create_time,
					'relays': [],
					'destroy': None
				}
			elif line[29:36] == "DESTROY":
				entry = parse_line(line)
				ident = entry['ident']
				record = records.get(ident)
				if record is not None:
					record['destroy'] = entry['time']
			elif line[29:33] == "RRC" + direc:
				entry = parse_line(line)
				record = records.get(entry['ident'])
				if record is not None:
					record['relays'].append(entry['time'])

		print "Removing invalid circuits"
		bad_circ_idents = set()
		for record in records.itervalues():
			if record['destroy'] is None or len(record['relays']) < 3:
				bad_circ_idents.add(record['ident'])
		filtered = filter(lambda rec: rec['ident'] not in bad_circ_idents,
			records.itervalues())
		print "** %i complete circuits total" % len(filtered)
		with open(outpath, 'w') as outfile:
			print "Dumping data to %s" % outpath
			json.dump(filtered, outfile)
