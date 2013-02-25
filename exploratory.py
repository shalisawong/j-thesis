from scipy.stats import skew, pearsonr
from numpy import mean, std, linspace
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib import cm
from pylab import get_cmap
from sklearn.cluster import k_means
from pprint import pprint
import sys, json, subprocess

cdict = {'red': 	((0, 0, 0),
                 	 (1, 1, 1)),
         'green': 	((0, 0, 0),
                 	 (1, 1, 1)),
         'blue': 	((0, 0, 0),
                 	 (1, 1, 1))}

my_cmap = LinearSegmentedColormap('my_colormap', cdict, 256)
artist_ident_map = {}
graphing_mode = sys.argv[1]
filepath = sys.argv[2]
bucket_size = int(sys.argv[3])
ts_ident = None
censor = None
discretize = False
n_bins = 0
use_labels = False

class IdentList(list):
	def __init__(self, ident):
		super(list, self).__init__()
		self.ident = ident

def onpick(event):
	ident = artist_ident_map[event.artist]
	print "Loading time series for circuit %s" % ident
	bash_call = "python exploratory.py -timeplot %s 1000 %i,%i" % (filepath, ident[0], ident[1])
	subprocess.call(bash_call, shell=True)

def bucketize(record, bucket_size):
	start = record['create']
	end = record['destroy']
	relays = record['relays']
	circ_len = end - start
	adj_times = [t - start for t in relays]
	first_relay = adj_times[0]
	last_relay = adj_times[-1]
	n_buckets = max(1, int(round(circ_len/bucket_size + .5)))
	bucketed = IdentList(record['ident'])

	# fill all buckets with 0 to start
	for i in xrange(0, n_buckets):
		bucketed.append(0)

	bucket_idx = 0
	window_end = bucket_size

	# fill buckets with relay cell counts
	for time in adj_times:
		if time < 0:
			raise ValueError("!!! Circuit %s had RELAY before CREATE" % record['ident'])
		elif time > circ_len:
			raise ValueError("!!! Circuit %s had RELAY after DESTROY" % record['ident'])
		if time > window_end:
			bucket_idx += 1
			window_end += bucket_size

		bucketed[bucket_idx] += 1

	return bucketed

def autocorrelate(values, lag=1):
	shifted = values[0:len(values)-1-lag]
	values_cutoff = values[lag:len(values)-1]
	return pearsonr(values_cutoff, shifted)

def avg_autocorr(values):
	avg = 0

	for lag in xrange(1, len(values)/4):
		corr = autocorrelate(values, lag)[0]
		avg += corr/len(values)

	return avg

def summarize(values, name):
	border_len = len(name) + 8
	print "*" * border_len
	print "***", name, "***"
	print "Mean:", mean(values)
	print "Min:", min(values)
	print "Max:" , max(values)
	print "Std Dev:", std(values)
	print "Skew:", skew(values)
	print "*" * border_len, "\n"

def seq_cmp(x, y):
	if len(x) == len(y):
		return 0
	elif len(x) > len(y):
		return 1
	else:
		return -1

if len(sys.argv) > 4:
	if graphing_mode == "-timeplot":
		cstr, ipstr = sys.argv[4].split(",")
		ts_ident = [int(cstr), int(ipstr)]
	elif sys.argv[4] == "-discretize":
		discretize = True
		n_bins = int(sys.argv[5])
		use_labels = sys.argv[6] == "-uselabels"
	else:
		censor = int(sys.argv[4])

with open(filepath) as data_file:
	circuits = json.load(data_file)

	# lists of descriptive statistics for individual series
	circ_len_aggr = []
	mean_cells_per_second_aggr = []
	min_cells_per_second_aggr = []
	max_cells_per_second_aggr = []
	stddev_cells_per_second_aggr = []
	skew_cells_per_second_agrr = []
	all_cells_per_second = []
	chosen_series = []

	print "Reading circuit data..."
	for circ in circuits:
		try:
			bucketized = bucketize(circ, bucket_size)
		except ValueError, e:
			print e
			continue

		circ_len = 1.0*(circ['destroy'] - circ['create'])

		# if max(bucketized) > 100:
		# 	continue

		if len(bucketized) > 0:
			if graphing_mode == '-summarize':
				circ_len_aggr.append(circ_len/1000)
				mean_cells_per_second_aggr.append(1.0*sum(bucketized)/circ_len)
				min_cells_per_second_aggr.append(min(bucketized))
				max_cells_per_second_aggr.append(max(bucketized))
				stddev_cells_per_second_aggr.append(std(bucketized))
			for sample in bucketized:
				all_cells_per_second.append(sample)

			chosen_series.append(bucketized)

	n_chosen = len(chosen_series)

	# Cluster the observations into k groups, then replace every value
	# with its corresponding centroid
	if discretize:
		vectorized = [[o] for o in all_cells_per_second]
		print "Clustering observations into discrete bins..."
		centroids, labels, inertia = k_means(vectorized, n_bins)
		print centroids
		print len(labels)
		# exit()
		idx = 0
		for circ in chosen_series:
			for i in xrange(0, len(circ)):
				label = labels[idx]
				centroid = centroids[label][0]

				if use_labels:
					circ[i] = label
				else:
					circ[i] = centroid

				idx += 1

	chosen_series.sort(cmp=seq_cmp)

	if graphing_mode == '-summarize':
		summarize(mean_cells_per_second_aggr, "Mean Cells/Second")
		summarize(circ_len_aggr, "Circuit Length (seconds)")

		lenplot = plt.subplot(311)
		plt.title("Circuit Time Frequencies")
		plt.xlabel("Circuit Time (seconds)")
		plt.ylabel("Number of Occurences")
		lenplot.hist(circ_len_aggr, bins=100)

		meansplot = plt.subplot(312)
		plt.title("Mean Cell/Second Frequencies")
		plt.xlabel("Mean Cells/Second")
		plt.ylabel("Number of Occurences")
		meansplot.hist(max_cells_per_second_aggr, bins=100)

		cellsplot = plt.subplot(313)
		plt.title("Instantaneous Cells/%ims Frequencies" % bucket_size)
		plt.xlabel("Instantaneous Cells/%ims" % bucket_size)
		plt.ylabel("Number of Occurences")
		cellsplot.hist(all_cells_per_second, bins=100)
	elif graphing_mode == '-timeplot':
		for series in chosen_series:
			if series.ident == ts_ident:
				plt.xlabel("Time (seconds)")
				plt.ylabel("Outgoing Relay Cells/Second")
				plt.fill_between(range(0, len(series)), series, [0]*len(series),
					color='grey')
	elif graphing_mode == '-horizon':
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', onpick)
		ax = fig.add_subplot(111)
		plt.title("Horizon Chart (n=%i)" % n_chosen)
		plt.grid(True)

		for series in chosen_series:
			ident = series.ident
			artist = ax.fill_between(range(0, len(series)), series, [0]*len(series),
				alpha=.1, color='black', edgecolor='none', picker=True)
			artist_ident_map[artist] = ident
	elif graphing_mode == '-colorplots':
		n = 1
		if not use_labels:
			vmin = 0
			vmax = censor or max(all_cells_per_second)
		else:
			vmin = 0
			vmax = n_bins
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', onpick)
		ax = fig.add_subplot(111)
		ax.patch.set_facecolor('grey')
		plt.title("Color Plots")
		for series in chosen_series:
			ident = series.ident
			scat = ax.scatter(range(0, len(series)), [n]*len(series),
				c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax,
				cmap=my_cmap, picker=True)
			artist_ident_map[scat] = ident
			n += 1
			if n == len(chosen_series)-1:
				plt.colorbar(scat)
	elif graphing_mode == '-autocorrs':
		vmin = -1
		vmax = 1
		i = 1
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', onpick)
		ax = fig.add_subplot(111)
		ax.patch.set_facecolor('black')
		did_bar = False
		for series in chosen_series:
			ident = series.ident
			lags = []
			correlations = []
			for lag in xrange(1, len(series)/4):
				correlation = autocorrelate(series, lag)[0]
				if not isnan(correlation):
					lags.append(lag)
					correlations.append(correlation)
			if len(lags) > 0:
				scat = ax.scatter(lags, [i]*len(lags), c=correlations, marker="s",
					edgecolors='none', vmin=vmin, vmax=vmax, cmap=my_cmap, picker=True)
				artist_ident_map[scat] = ident
				i += 1
				if not did_bar:
					plt.colorbar(scat)
					did_bar = True
	else:
		print "ERROR: Invalid graphing mode selected"

	plt.show()
