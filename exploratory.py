from scipy.stats import skew, pearsonr
from numpy import mean, std, linspace
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Rectangle
from pylab import get_cmap
from sklearn.cluster import k_means
from pprint import pprint
import sys, json, subprocess

n_bins = 6
cdict = {'red':    ((0, 0, 0),
                   (1, .9, 1)),
         'green':  ((0, 0, 0),
                   (1, .9, 1)),
         'blue':   ((0, 0, 0),
                   (1, .9, 1))}
continuous_cmap = LinearSegmentedColormap('my_colormap', cdict, 256)
discrete_colors =[(1.0*i/n_bins, 1.0*i/n_bins, 1.0*i/n_bins) for i in xrange(1, n_bins+1)]
discrete_cmap = ListedColormap(discrete_colors)
artist_ident_map = {}

class IdentList(list):
	def __init__(self, ident):
		super(list, self).__init__()
		self.ident = ident

def on_pick(event):
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

def summarize(values, name):
	border_len = len(name) + 8
	print "*" * border_len
	print "***", name, "***"
	print "Mean:", mean(values)
	print "Min:", min(values)
	print "Max:" , max(values)
	print "Std Dev:", std(values)
	print "*" * border_len, "\n"

def seq_cmp(x, y):
	if len(x) == len(y):
		return 0
	elif len(x) > len(y):
		return 1
	else:
		return -1

graphing_mode = sys.argv[1]
filepath = sys.argv[2]
bucket_size = int(sys.argv[3])
ts_ident = None
discretize = False
clip_limit = float("inf")
cluster_maxes = [0] * n_bins
cluster_mins = [float("inf")] * n_bins
true_max = 0

if graphing_mode == "-timeplot":
	if len(sys.argv) > 4:
		cstr, ipstr = sys.argv[4].split(",")
		ts_ident = [int(cstr), int(ipstr)]
elif graphing_mode == '-colorplots':
	discretize = True
	if len(sys.argv) > 4:
		clip_limit = int(sys.argv[4])

with open(filepath) as data_file:
	circuits = json.load(data_file)

	# lists of descriptive statistics for individual series
	circ_len_aggr = []
	mean_cells_per_second_aggr = []
	min_cells_per_second_aggr = []
	max_cells_per_second_aggr = []
	stddev_cells_per_second_aggr = []
	skew_cells_per_second_agrr = []
	all_cells_per_bucket = []
	chosen_series = []

	print "Reading circuit data..."
	for circ in circuits:
		try:
			bucketized = bucketize(circ, bucket_size)
		except ValueError, e:
			print e
			continue

		circ_len = 1.0*(circ['destroy'] - circ['create'])

		if len(bucketized) > 0:
			if graphing_mode == '-summarize':
				circ_len_aggr.append(circ_len/1000)
				mean_cells_per_second_aggr.append(1.0*sum(bucketized)/circ_len)
				min_cells_per_second_aggr.append(min(bucketized))
				max_cells_per_second_aggr.append(max(bucketized))
				stddev_cells_per_second_aggr.append(std(bucketized))
			for i in xrange(0, len(bucketized)):
				orig_sample = bucketized[i]
				true_max = max(true_max, orig_sample)
				clipped_sample = min(bucketized[i], clip_limit)
				bucketized[i] = clipped_sample
				all_cells_per_bucket.append(clipped_sample)

			chosen_series.append(bucketized)

	n_chosen = len(chosen_series)

	# Cluster the observations into k groups, then replace every value
	# with its corresponding cluster label
	if discretize:
		vectorized = [[o] for o in all_cells_per_bucket]
		print "Clustering observations into discrete bins..."
		centroids, labels, inertia = k_means(vectorized, n_bins)
		idx = 0
		for circ in chosen_series:
			for i in xrange(0, len(circ)):
				label = labels[idx]
				cluster_maxes[label] = max(cluster_maxes[label], circ[i])
				cluster_mins[label] = min(cluster_mins[label], circ[i])
				circ[i] = label
				idx += 1

	cluster_ranges = zip(sorted(cluster_mins), sorted(cluster_maxes))
	cluster_ranges[-1] = (cluster_ranges[-1][0], true_max)
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
		cellsplot.hist(all_cells_per_bucket, bins=100)
	elif graphing_mode == '-timeplot':
		fig = plt.figure()
		fig.canvas.set_window_title("%i-%i-%i" % (ts_ident[0], ts_ident[1],
			bucket_size))
		ax = fig.add_subplot(111)
		for series in chosen_series:
			if series.ident == ts_ident:
				plt.xlabel("Window # (%i ms windows)" % bucket_size)
				plt.ylabel("Outgoing Relay Cell Count")
				ax.fill_between(range(0, len(series)), series, [0]*len(series),
					color='grey')
	elif graphing_mode == '-horizon':
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', on_pick)
		ax = fig.add_subplot(111)
		plt.title("Horizon Chart (n=%i)" % n_chosen)
		plt.xlabel("Window # (%i ms windows)" % bucket_size)
		plt.ylabel("Outgoing Relay Cells/Second")
		plt.grid(True)

		for series in chosen_series:
			ident = series.ident
			# use fill_between to avoid some rendering bugs
			artist = ax.fill_between(range(0, len(series)), series, [0]*len(series),
				alpha=.1, color='black', edgecolor='none', picker=True)
			artist_ident_map[artist] = ident
	elif graphing_mode == '-colorplots':
		n = 1
		vmin = 0
		vmax = n_bins
		legend_rects = [Rectangle((0, 0), 1, 1, fc=c) for c in reversed(discrete_colors)]
		legend_labels = ["%i-%i cells" % c for c in reversed(cluster_ranges)]
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', on_pick)
		ax = fig.add_subplot(111)
		# ax.patch.set_facecolor('grey')
		ax.get_yaxis().set_ticks([])
		if clip_limit < float('inf'):
			plt.title("Color Plots (clip limit = %s)" % clip_limit)
		else:
			plt.title("Color Plots")
		plt.xlabel("Window # (%i ms windows)" % bucket_size)
		plt.ylabel("Client")
		plt.legend(legend_rects, legend_labels, loc=4)
		for series in chosen_series:
			ident = series.ident
			scat = ax.scatter(range(0, len(series)), [n]*len(series),
				c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax,
				cmap=discrete_cmap, picker=True)
			artist_ident_map[scat] = ident
			n += 1
	elif graphing_mode == '-autocorrs':
		vmin = -1
		vmax = 1
		i = 1
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', on_pick)
		ax = fig.add_subplot(111)
		# ax.patch.set_facecolor('white')
		plt.title("Autocorrelation Color Plot")
		plt.xlabel("Lag" % bucket_size)
		plt.ylabel("Client")
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
					edgecolors='none', vmin=vmin, vmax=vmax, cmap=continuous_cmap, picker=True)
				artist_ident_map[scat] = ident
				i += 1
				if not did_bar:
					plt.colorbar(scat)
					did_bar = True
	else:
		print "ERROR: Invalid graphing mode selected"

	plt.show()
