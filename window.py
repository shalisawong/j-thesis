"""
Window the sequences in JSON a file output by logparse.py
Syntax: python writebucketized infile window_size outfile
window_size is in milliseconds.
@author Julian Applebaum
"""

from pprint import pprint
import sys, json

def window(record, window_size):
	"""
	Window a circuit's relay cell time series.
	@param record: The record encoding the time series
	@param: window_size: The length, in milliseconds, of each window
	@return: The windowed version of the time series component.
	"""
	start = record['create']
	end = record['destroy']
	relays = record['relays']
	circ_len = end - start
	# make all times relative to the last CREATE cell sent
	adj_times = [t - start for t in relays]
	first_relay = adj_times[0]
	last_relay = adj_times[-1]
	if first_relay < 0:
		raise ValueError("!!! Circuit %s had RELAY before CREATE" % record['ident'])
	elif last_relay > circ_len:
		raise ValueError("!!! Circuit %s had RELAY after DESTROY" % record['ident'])
	n_windows = max(1, int(round(circ_len/window_size + .5)))
	windowed = []
	# fill all windows with 0 to start
	for i in xrange(0, n_windows):
		windowed.append(0)
	window_idx = 0
	window_end = window_size
	# fill windows with relay cell counts
	for time in adj_times:
		if time > window_end:
			window_idx += 1
			window_end += window_size
		windowed[window_idx] += 1
	return windowed

if __name__ == "__main__":
	filepath = sys.argv[1]
	window_size = int(sys.argv[2])
	outpath = sys.argv[3]
	with open(filepath) as data_file:
		with open(outpath, 'w') as out_file:
			print "Loading circuit data..."
			circuits = json.load(data_file)
			print "Windowing %i circuits" % len(circuits)
			good_circs = []
			for i in xrange(0, len(circuits)):
				print "Circuit %i" % i
				circ = circuits[i]
				try:
					windowed = window(circ, window_size)
					circ['relays'] = windowed
					good_circs.append(circ)
				except ValueError, e:
					print e
			print "Dumping to %s" % outpath
			json.dump(good_circs, out_file)
