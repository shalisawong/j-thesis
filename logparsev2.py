import sys, datetime, json

# takes a time string and returns the number of milliseconds since the epoch
def parse_time(time_str):
    # time string needs a year, and the format string needs time in nanoseconds,
    # but the time string is in milliseconds, so add some zeroes.
    s = '2010 ' + time_str + '000'
    d = datetime.datetime.strptime(s,'%Y %b %d %H:%M:%S.%f')
    # (approx) milliseconds since the epoch
    st = int(d.strftime('%s'))*1000 + (d.microsecond/1000)
    if len(str(st)) != 13: print s,d,st
    return st

def parse_line(line):
	split = line.split(" ")
	circid = int(split[5])
	ipslug = int(split[6])
	time = parse_time(line[0:18])
	return {
		'ident': (circid, ipslug),
		'time': time
	}

lfpath = sys.argv[1]
outpath = sys.argv[2]
direc = sys.argv[3].upper()

with open(lfpath) as logfile:
	print "Reading file..."
	lines = logfile.read().split("\n")
	created_circs = set()
	time_series = {} # map circuit idents to time series
	zero_circ_ids = []

	print "Parsing..."
	# first pass - determine which circuits are complete
	for line in lines:
		if line[29:35] == "CREATE":
			record = parse_line(line)
			created_circs.add(record['ident'])
		elif line[29:36] == "DESTROY":
			parsed = parse_line(line)
			ident = record['ident']
			if ident in created_circs:
				time_series[ident] = []

	# second pass - build time series for complete circuits
	for line in lines:
		if line[29:33] == "RRC" + direc:
			record = parse_line(line)
			series = time_series.get(record['ident'])
			if series is not None:
				series.append(record['time'])



	# third pass - identify length 0 series
	for ident, series in time_series.iteritems():
		if len(series) == 0:
			zero_circ_ids.append(ident)

	for ident in zero_circ_ids:
		del time_series[ident]

	percent_complete = 100 * 1.0*len(time_series)/len(created_circs)

	print "** There were %i circuits total" % len(created_circs)
	print "** %i of the circuits had CREATE and DESTROY, but no RELAY" % len(zero_circ_ids)
	print "** %d%% (%i) of the circuits were complete" % (percent_complete,
		len(time_series))

	with open(outpath, 'w') as outfile:
		print "Dumping data to %s" % outpath
		json.dump(time_series.values(), outfile)




