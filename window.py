"""
Window the sequences from a logparse.py output file. Outputs a pickled dict:
{ 'window_size': window_size
  'records': same as input, but with 'relay_in' and 'relay_out' replaced by
  			 their windowed versions }

	Syntax: python window.py infile outfile window_size
window_size is in milliseconds.

@author: Julian Applebaum
"""

from pprint import pprint
from multiprocessing import Pool
import sys, cPickle

def window_record(pair):
	"""
	Window a record's incoming and outgoing relay time series:
	@param pair: A pair (record, window_size)
	@return: The same record, but with both time series replaced by
		series of window_size cell counts
	"""
	record, window_size = pair
	ident, create, destroy = record['ident'], record['create'], record['destroy']
	relays_in, relays_out = record['relays_in'], record['relays_out']
	#windowed_in = window_relays(create, destroy, relays_in, window_size)
	#windowed_out = window_relays(create, destroy, relays_out, window_size)
	windowed_both = window_allrelays(create, destroy, relays_in, relays_out, window_size)
	#print windowed_in, windowed_out, windowed_both
	#return {
	#	'ident': ident,
	#	'create': create,
	#	'destroy': destroy,
	#	'relays_in': windowed_in,
	#	'relays_out': windowed_out
	#}
	return {
		'ident': ident,
		'create': create,
		'destroy': destroy,
		'relays': windowed_both
	}

def window_allrelays(create, destroy, relays_in, relays_out, window_size):
	"""
	"""
	circ_len = destroy - create
	# make all times relative to last CREATE cell sent
	adj_times_in = [t - create for t in relays_in]
	adj_times_out = [t - create for t in relays_out]
	n_windows = max(1, int(round(circ_len/window_size + .5)))
	windows = []
	# fill all windows with (0,0) to start
	for i in xrange(0, n_windows):
		windows.append([0,0])
	window_idx = 0
	window_end = window_size
	# fill windows with relay in cell counts
	for time in adj_times_in:
		if time > window_end:
			window_idx += 1
			window_end += window_size
		windows[window_idx][0] += 1
	# fill windows with relay out cell counts
	window_idx = 0
	window_end = window_size
	for time in adj_times_out:
		if time > window_end:
			window_idx += 1
			window_end += window_size
		windows[window_idx][1] += 1

	# convert from list to tuple
	return [tuple(p) for p in windows]

def window_relays(create, destroy, relays, window_size):
	"""
	Window a relay cell time series.
	@param create: the timestamp of the last CREATE received
	@param destroy: the timestamp of the first DESTROY received
	@param relays: the RELAY cell time series
	@param: window_size: The length, in milliseconds, of each window
	@return: The windowed version of the relay time series.
	"""
	circ_len = destroy - create
	# make all times relative to the last CREATE cell sent
	adj_times = [t - create for t in relays]
	n_windows = max(1, int(round(circ_len/window_size + .5)))
	windows = []
	# fill all windows with 0 to start
	for i in xrange(0, n_windows):
		windows.append(0)
	window_idx = 0
	window_end = window_size
	# fill windows with relay cell counts
	for time in adj_times:
		if time > window_end:
			window_idx += 1
			window_end += window_size
		windows[window_idx] += 1
	return windows

if __name__ == "__main__":
	inpath = sys.argv[1]
	outpath = sys.argv[2]
	window_size = int(sys.argv[3])
	pool = Pool()
	with open(inpath) as data_file:
		print "Loading circuit data..."
		records = cPickle.load(data_file)

	with open(outpath, 'w') as out_file:
		print "Windowing %i circuits (parallel)..." % len(records)
		map_items = zip(records, [window_size] * len(records))
		windowed = pool.map(window_record, map_items)
		#print windowed
		print "Done"
		output = {
			'window_size': window_size,
			'records': windowed
		}
		print "Dumping to %s" % outpath
		cPickle.dump(output, out_file, protocol=2
			)
