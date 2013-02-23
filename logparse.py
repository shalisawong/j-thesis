from datetime import datetime
import sys, json

# takes a time string and returns the number of milliseconds since the epoch
def parse_time(time_str):
    augmented = '2013 ' + time_str
    date_parsed = datetime.strptime(augmented[0:-4],'%Y %b %d %H:%M:%S')
    n_seconds = 1.0*(date_parsed - datetime(2013, 1, 1)).total_seconds()
    n_milliseconds = int(time_str[-3:])
    return 1000*n_seconds + n_milliseconds

def parse_line(line):
	split = line.split(" ")
	circid = int(split[5])
	ipslug = int(split[6])
	time = parse_time(line[0:19])
	return {
		'ident': (circid, ipslug),
		'time': time
	}

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
	# first pass - determine which circuits are complete
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
					'create': create_time,
					'relays': [],
					'destroy': destroy_time
				}


	logfile.seek(0)

	# second pass - build time series for complete circuits
	for line in logfile:
		if line[29:33] == "RRC" + direc:
			record = parse_line(line)
			series = time_series.get(record['ident'])
			if series is not None:
				series['relays'].append(record['time'])


	n_incomplete = len(create_times) - len(time_series)

	# third pass - delete circuits with no relay cells
	for ident, record in time_series.iteritems():
		if len(record['relays']) == 0:
			zero_circ_ids.append(ident)

	for ident in zero_circ_ids:
		del time_series[ident]

	percent_complete = 100 * 1.0*len(time_series)/len(create_times)

	print "** There were %i circuits total" % len(create_times)
	print "** %i circuits only had CREATE cells" % n_incomplete
	print "** %i circuits had CREATE and DESTROY, but no RELAY" % len(zero_circ_ids)
	print "** %d%% (%i) circuits had CREATE, RELAY, and DESTROY" % (percent_complete,
		len(time_series))

	with open(outpath, 'w') as outfile:
		print "Dumping data to %s" % outpath
		json.dump(time_series.values(), outfile)
