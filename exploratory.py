from scipy.stats import skew, pearsonr
from numpy import mean, std, linspace, correlate
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Rectangle
from pylab import get_cmap
from sklearn.cluster import k_means
from pprint import pprint
from math import isnan, log
import sys, json, subprocess

BUCKET_SIZE = 5000
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
	"""
	A list that can be tagged with a circuit id, ip address pair. Used
	to represent the time series for a circuit.
	@ivar ident: the id, ip pair identifying the circuit
	"""
	def __init__(self, *args):
		if len(args) == 1:
			list.__init__(self)
			self.ident = args[0]
		elif len(args) == 2:
			list.__init__(self, args[0])
			self.ident = args[1]

def on_pick(event):
	"""
	Pull up the time plot for a series when the user clicks on it.
	@param event: The picking event fired by the click
	"""
	ident = artist_ident_map[event.artist]
	print "Loading time series for circuit %s" % ident
	bash_call = "python exploratory.py -timeplot %s 1000 %i,%i" % (filepath, ident[0], ident[1])
	subprocess.call(bash_call, shell=True)

def autocorrelate(values, lag=1):
	shifted = values[0:len(values)-1-lag]
	values_cutoff = values[lag:len(values)-1]
	val = pearsonr(values_cutoff, shifted)
	print val[1]
	return val[0]

def acorr_plot(series, ax):
	corrs = []
	for i in xrange(1, len(series)/4):
		corrs.append(autocorrelate(series, i))
	plt.xlabel("Lag")
	plt.ylabel("Pearson Correlation")
	ax.bar(range(1, len(corrs)+1), corrs, width=1)
	plt.ylim([-1, 1])

def summarize(values, name):
	"""
	Print out summary states for a list of values

	@param values: The values to summarize
	@param name: The name to display in the printed text
	"""
	border_len = len(name) + 8
	print "*" * border_len
	print "***", name, "***"
	print "Mean:", mean(values)
	print "Min:", min(values)
	print "Max:" , max(values)
	print "Std Dev:", std(values)
	print "*" * border_len, "\n"

def seq_cmp(x, y):
	"""
	Order sequences by their length, ascending

	@param x: a sequence
	@param y: a sequence
	@return: 1 if len(x) > len(y), 0 of len(x) = len(y), 0 otherwise
	"""
	if len(x) == len(y):
		return 0
	elif len(x) > len(y):
		return 1
	else:
		return -1

if __name__ == "__main__":
	graphing_mode = sys.argv[1]
	filepath = sys.argv[2]
	bucket_size = BUCKET_SIZE
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
		print "Parsing JSON file..."
		circuits = json.load(data_file)

		# lists of descriptive statistics for individual series
		circ_len_aggr = []
		mean_cells_per_bucket_aggr = []
		min_cells_per_bucket_aggr = []
		max_cells_per_bucket_aggr = []
		stddev_cells_per_bucket_aggr = []
		all_cells_per_bucket = []
		chosen_series = []

		print "Reading circuit data..."
		for circ in circuits:
			bucketized = IdentList(circ['relays'], circ['ident'])

			if graphing_mode == '-summarize':
				circ_len = 1.0*(circ['destroy'] - circ['create'])
				circ_len_aggr.append(circ_len/1000)
				mean_cells_per_bucket_aggr.append(1.0*sum(bucketized)/len(bucketized))
				min_cells_per_bucket_aggr.append(min(bucketized))
				max_cells_per_bucket_aggr.append(max(bucketized))
				stddev_cells_per_bucket_aggr.append(std(bucketized))
			for i in xrange(0, len(bucketized)):
				orig_sample = bucketized[i]
				true_max = max(true_max, orig_sample)
				clipped_sample = min(bucketized[i], clip_limit)
				bucketized[i] = clipped_sample
				all_cells_per_bucket.append(clipped_sample)

			chosen_series.append(bucketized)

		n_chosen = len(chosen_series)
		print "%i time series" % n_chosen

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

		print "Graphing..."
		if graphing_mode == '-summarize':
			summarize(mean_cells_per_bucket_aggr, "Mean Cells/Bucket")
			summarize(all_cells_per_bucket, "Instantaneous Cell Count")
			summarize(circ_len_aggr, "Circuit Length (seconds)")

			fig = plt.figure()

			lenplot = fig.add_subplot(321)
			plt.title("Circuit Times")
			plt.xlabel("Circuit Time (seconds)")
			plt.ylabel("Frequency")
			plt.yscale('log')
			lenplot.hist(circ_len_aggr, bins=100)

			meansplot = fig.add_subplot(322)
			plt.title("Mean Cells/Bucket")
			plt.xlabel("Mean Cells/Bucket")
			plt.ylabel("Frequency")
			plt.yscale('log')
			meansplot.hist(mean_cells_per_bucket_aggr, bins=100)

			minsplot = fig.add_subplot(323)
			plt.title("Min Cells/Bucket")
			plt.xlabel("Min Cells/Bucket")
			plt.ylabel("Frequency")
			plt.yscale('log')
			minsplot.hist(min_cells_per_bucket_aggr, bins=100)

			maxsplot = fig.add_subplot(324)
			plt.title("Max Cells/Bucket")
			plt.xlabel("Max Cells/Bucket")
			plt.ylabel("Frequency")
			plt.yscale('log')
			maxsplot.hist(max_cells_per_bucket_aggr, bins=100)

			stddevsplot = fig.add_subplot(325)
			plt.title("Std Dev. of Cells/Bucket")
			plt.xlabel("Std Dev. Cells/Bucket")
			plt.ylabel("Frequency")
			plt.yscale('log')
			stddevsplot.hist(stddev_cells_per_bucket_aggr, bins=100)

			cellsplot = fig.add_subplot(326)
			plt.title("Instantaneous Cell Count")
			plt.xlabel("Instantaneous Cell Count")
			plt.ylabel("Frequency")
			plt.yscale('log')
			cellsplot.hist(all_cells_per_bucket, bins=100)

			fig.tight_layout()
		elif graphing_mode == '-timeplot':
			fig = plt.figure()
			fig.canvas.set_window_title("%i-%i-%i" % (ts_ident[0], ts_ident[1],
				bucket_size))
			timeplot = fig.add_subplot(121)
			acorrplot = fig.add_subplot(122)
			for series in chosen_series:
				if series.ident == ts_ident:
					plt.xlabel("Window # (%i ms windows)" % bucket_size)
					plt.ylabel("Outgoing Relay Cell Count")
					timeplot.fill_between(range(0, len(series)), series, [0]*len(series),
						color='grey')
					acorr_plot(series, acorrplot)

		elif graphing_mode == '-horizon':
			fig = plt.figure()
			fig.canvas.mpl_connect('pick_event', on_pick)
			ax = fig.add_subplot(111)
			plt.title("Horizon Chart (n=%i)" % n_chosen)
			plt.xlabel("Window # (%i ms windows)" % bucket_size)
			plt.ylabel("Outgoing Relay Cells/Bucket")
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
			plt.title("Autocorrelation Color Plot")
			plt.xlabel("Lag")
			plt.ylabel("Client")
			did_bar = False
			for series in chosen_series:
				ident = series.ident
				lags = []
				correlations = []
				for lag in xrange(1, len(series)/4):
					correlation = autocorrelate(series, lag)
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
