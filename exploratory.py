"""
Create visualizations for time series data from parsed, windowed log files.
Supports horizon plots and color plots for random samples, histogram of
distribution characteristics, and single series time plots.
	Syntax: python exploratory.py -summarize logfile.pickle cell_direc
			python exploratory.py -horizon logfile.pickle cell_direc rand_seed
			python exploratory.py -colorplots logfile.pickle cell_direc rand_seed
			python exploratory.py -timeplot logfile.pickle cell_direc ts_ident
cell_direc is either "O" for outgoing, or "I" for incoming. rand_seed determines
which 1000 series random sample is taken from the record set. ts_ident is the
identifier of the single series to view, in the format 'circ_id,ip_slug'.
@author: Julian Applebaum
"""

from scipy.stats import skew, pearsonr
from numpy import mean, std, median, linspace, correlate
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Rectangle
from sklearn.cluster import k_means
from pprint import pprint
from math import sqrt
from sequence_utils import trim_inactive, flatten
import matplotlib.pyplot as plt
from matplotlib import cm
import pylab
import sys, cPickle, subprocess, random
from glob import glob

N_HIST_BINS = 100
N_CLUSTERS = 6
VMAX = 700
MAX_OBS = 1500
artist_ident_map = {}

def draw_sample(data, n=1000):
	"""
	Draw a random sample from a list
	@param data: the list
	@param n: the size of the sample
	@return: a size n random sample of data
	"""
	random.shuffle(data)
	return data[:n]

def on_pick(event):
	"""
	Pull up the time plot for a series when the user clicks on it.
	@param event: The picking event fired by the click
	"""
	ident = artist_ident_map[event.artist]
	print "Loading time series for circuit %s" % ident
	bash_call = "python exploratory.py -timeplot %s 1000 %i,%i" % (filepath,
		ident[0], ident[1])
	subprocess.call(bash_call, shell=True)

def autocorrelate(series, lag=1):
	"""
	Perform Pearson autocorrelation on a time series
	@param series: the time series
	@param lag: the lag
	@return: the autocorrelation coefficient
	"""
	shifted = series[0:len(series)-1-lag]
	series_cutoff = series[lag:len(series)-1]
	return pearsonr(series_cutoff, shifted)[0]

def acorr_plot(series, ax):
	"""
	Generate a correlogram for a series for all possible lag values.
	@param series: the time series
	@param ax: the axes object to draw the plot on
	"""
	corrs = []
	for i in xrange(1, len(series)-1):
		corrs.append(autocorrelate(series, i))
	plt.title("Correlogram")
	plt.xlabel("Lag")
	plt.ylabel("Pearson Correlation")
	ax.bar(range(1, len(corrs)+1), corrs, width=1)
	plt.ylim([-1, 1])

def summarize(values, name):
	"""
	Print out summary stats for a list of values
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

def discretize(relay_series):
	"""
	Cluster the observations in relay_series into k bins, and replace each
	observation with its cluster label.
	@param relay_series: the list of series to discretize
	@param k: the number of clusters to create
	@return: (relay_series, cluster_ranges). relay_series is the list of
		discretized series. cluster_ranges is a list of cluster mins and maxs
		in s.t. cluster_ranges[i] = (min(cluster_i), max(cluster_i))
	"""
	cluster_maxes = [0 for i in xrange(0, k)]
	cluster_mins = [float("inf") for i in xrange(0, k)]
	all_window_counts = reduce(list.__add__, relay_series, [])
	vectorized = [[o] for o in all_window_counts]
	idx = 0
	for series in relay_series:
		for i in xrange(0, len(series)):
			label = labels[idx]
			cluster_maxes[label] = max(cluster_maxes[label], series[i])
			cluster_mins[label] = min(cluster_mins[label], series[i])
			series[i] = label
			idx += 1
	cluster_ranges = zip(sorted(cluster_mins), sorted(cluster_maxes))
	return (relay_series, cluster_ranges)

def do_summarize(records, direc_key):
	"""
	Display summary histograms for the series in records.
	@param records: the circuit records
	@param direc_key: 'relays_in' for incoming relays, 'relays_out' for
		outgoing
	"""
	circ_len_aggr = []
	mean_cells_per_window_aggr = []
	min_cells_per_window_aggr = []
	max_cells_per_window_aggr = []
	median_cells_per_window_aggr = []
	stddev_cells_per_window_aggr = []
	inst_counts_aggr = []
	unique_vals_aggr = []
	percent_active_aggr = []
	time_active_aggr = []
	for record in records:
		relays = record[direc_key]
		circ_len_aggr.append((record['destroy'] - record['create'])/1000.0)
		mean_cells_per_window_aggr.append(1.0*sum(relays)/len(relays))
		median_cells_per_window_aggr.append(median(relays))
		min_cells_per_window_aggr.append(min(relays))
		max_cells_per_window_aggr.append(max(relays))
		stddev_cells_per_window_aggr.append(std(relays))
		inst_counts_aggr += relays
		# unique_vals_aggr.append(len(set(filter(lambda o: o > 2, relays))))
		time_active = len(trim_inactive(relays))
		percent_active_aggr.append(100.0*time_active/len(relays))
		# time_active_aggr.append(time_active)
	fig = plt.figure()
	summarize(max_cells_per_window_aggr, "Max")

	meansplot = fig.add_subplot(421)
	plt.title("Mean Cells/Window")
	plt.xlabel("Mean Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	meansplot.hist(mean_cells_per_window_aggr, bins=N_HIST_BINS)

	cellsplot = fig.add_subplot(422)
	plt.title("Median Cells/Window")
	plt.xlabel("Median Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	cellsplot.hist(median_cells_per_window_aggr, bins=N_HIST_BINS)

	minsplot = fig.add_subplot(423)
	plt.title("Min Cells/Window")
	plt.xlabel("Min Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	minsplot.hist(min_cells_per_window_aggr, bins=N_HIST_BINS)

	maxsplot = fig.add_subplot(424)
	plt.title("Max Cells/Window")
	plt.xlabel("Max Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	maxsplot.hist(max_cells_per_window_aggr, bins=N_HIST_BINS)

	stddevsplot = fig.add_subplot(425)
	plt.title("Std Dev. of Cells/Window")
	plt.xlabel("Std Dev. of Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	stddevsplot.hist(stddev_cells_per_window_aggr, bins=N_HIST_BINS)

	cellsplot = fig.add_subplot(426)
	plt.title("Single Window Cell Count")
	plt.xlabel("Single Window Cell Count")
	plt.ylabel("Frequency")
	plt.yscale('log')
	cellsplot.hist(inst_counts_aggr, bins=N_HIST_BINS)

	lenplot = fig.add_subplot(427)
	plt.title("Circuit Length (seconds)")
	plt.xlabel("Circuit Length (seconds)")
	plt.ylabel("Frequency")
	plt.yscale('log')
	lenplot.hist(circ_len_aggr, bins=N_HIST_BINS)

	# uniqueplot = fig.add_subplot(338)
	# plt.title("Number of Unique Values > 1")
	# plt.xlabel("Number of Unique Values > 1")
	# plt.ylabel("Frequency")
	# uniqueplot.hist(unique_vals_aggr, bins=N_HIST_BINS)

	# timeactiveplot = fig.add_subplot(428)
	# plt.title("Percent of Time in Active State")
	# plt.xlabel("Percent of Time")
	# plt.ylabel("Frequency")
	# timeactiveplot.hist(percent_active_aggr, bins=N_HIST_BINS)
	fig.tight_layout()

def do_horizon(records, direc_key, window_size, ylim=None):
	"""
	Display a horizon plot for a size 1000 random sample of records
	@param records: the circuit records
	@param direc_key: 'relays_in' for incoming relays, 'relays_out' for
		outgoing
	@param window_size: the size of the cell count windows
	"""
	sample = draw_sample(records)
	fig = plt.figure()
	fig.canvas.mpl_connect('pick_event', on_pick)
	ax = fig.add_subplot(111)
	plt.title("Horizon Plot (n=%i)" % len(sample))
	plt.xlabel("Window # (%i ms windows)" % window_size)
	plt.ylabel("Outgoing Relay Cells/Window")
	plt.grid(True)
	for record in sample:
		series = record[direc_key]
		# use fill_between to avoid some rendering bugs
		artist = ax.fill_between(range(0, len(series)), series, [0]*len(series),
			alpha=.2, color='black', edgecolor='none', picker=True)
		artist_ident_map[record['ident']] = artist
	if ylim is not None:
		pylab.ylim([0, ylim])

def do_timeplot(records, direc_key, window_size, ts_ident):
	"""
	Display a time plot and a correlogram for one time series
	@param records: the list of circuits records containing the series
	@param direc_key: 'relays_in' for incoming relays, 'relays_out' for
		outgoing
	@param window_size: the size of the cell count windows
	@param ts_ident: the (circ_id, ip_slug) tuple identifying the series
	"""
	fig = plt.figure()
	fig.canvas.set_window_title("%i-%i-%i" % (ts_ident[0], ts_ident[1],
		window_size))
	timeplot = fig.add_subplot(111)
	# acorrplot = fig.add_subplot(122)
	for record in records:
		if record['ident'] == ts_ident:
			plt.xlabel("Window # (%i ms windows)" % window_size)
			plt.ylabel("Outgoing Relay Cell Count")
			series = record[direc_key]
			timeplot.fill_between(range(0, len(series)), series, [0]*len(series),
				color='grey')
			# acorr_plot(series, acorrplot)

def do_colorplot(records, direc_key, window_size, ax=None, no_chrome=False,
	sample_size=1000):
	"""
	Display a color plots for a size 1000 random sample of records
	@param records: the circuit records
	@param direc_key: 'relays_in' for incoming relays, 'relays_out' for
		outgoing
	@param window_size: the size of the cell count windows
	"""
	def rec_cmp(rec_1, rec_2):
		relays_1, relays_2 = rec_1[direc_key], rec_2[direc_key]
		m_r1, m_r2= mean(relays_1), mean(relays_2)
		if len(relays_1) == len(relays_2):
			if m_r1 == m_r2: return 0
			elif m_r1 > m_r2: return 1
			else: return -1
		elif len(relays_1) > len(relays_2):
			return 1
		else:
			return -1
	sample = draw_sample(records, sample_size)
	sample.sort(cmp=rec_cmp)
	N_CLUSTERS = 6
	colors =[(1.0*i/N_CLUSTERS,)*3 for i in xrange(1, N_CLUSTERS+1)]
	cmap = ListedColormap(colors)
	relay_series = [record[direc_key] for record in sample]
	vmin = 0
	vmax = VMAX
	if ax is None:
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', on_pick)
		ax = fig.add_subplot(111)
		ax.get_yaxis().set_ticks([])
	if not no_chrome:
		plt.title("Luminance Plot (n=%i)" % len(sample))
		plt.xlabel("Window # (%i ms windows)" % window_size)
		plt.ylabel("Client")
		# legend_rects = [Rectangle((0, 0), 1, 1, fc=c) for c in reversed(colors)]
		# legend_labels = ["%i-%i cells" % c for c in reversed(cluster_ranges)]
		# plt.legend(legend_rects, legend_labels, loc=4)
	n = 0
	for i in xrange(0, len(sample)):
		series = relay_series[i]
		ident = sample[i]['ident']
		artist = ax.scatter(range(0, len(series)), [n]*len(series),
			c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax,
			cmap=cm.coolwarm, picker=True)
		n += 2
		artist_ident_map[ident] = artist
	if not no_chrome:
		fig.colorbar(artist)

if __name__ == "__main__":
	graphing_mode = sys.argv[1]
	inpath = sys.argv[2]
	direc = sys.argv[3].upper()
	if len(sys.argv) > 4: seed = int(sys.argv[4])
	else: seed = 0
	print "Random seed =", seed
	random.seed(seed)
	if direc == "I":
		direc_key = 'relays_in'
	elif direc == "O":
		direc_key = 'relays_out'
	else:
		print "Invalid cell direction"
		exit()
	with open(inpath) as data_file:
		print "Reading data..."
		data = cPickle.load(data_file)
	window_size, records = data['window_size'], data['records']
	if graphing_mode == "-timeplot":
		cstr, ipstr = sys.argv[4].split(",")
		ts_ident = (int(cstr), int(ipstr))
	elif graphing_mode == "-agg-colorplots":
		k_val = int(sys.argv[4])
		records = filter(lambda r: r['ident'] == (k_val, k_val), records)
	print "%i series" % len(records)
	print "Graphing..."
	if graphing_mode == '-summarize':
		do_summarize(records, direc_key)
	elif graphing_mode == '-horizon':
		do_horizon(records, direc_key, window_size)
	elif graphing_mode == '-timeplot':
		do_timeplot(records, direc_key, window_size, ts_ident)
	elif graphing_mode == '-colorplots':
		do_colorplot(records, direc_key, window_size)
	elif graphing_mode == '-agg-colorplots':
		do_colorplot(records, direc_key, window_size)
		do_horizon(records, direc_key, window_size, MAX_OBS)
	else:
		print "ERROR: Invalid graphing mode selected"
	plt.show()
