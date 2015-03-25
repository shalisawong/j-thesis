"""
Create visualizations for time series data from parsed, windowed log files.
Supports horizon plots and color plots for random samples, histogram of
distribution characteristics, and single series time plots.
	Syntax: python exploratory.py -summarize logfile.pickle 
			python exploratory.py -horizon logfile.pickle rand_seed
			python exploratory.py -colorplots logfile.pickle rand_seed
			python exploratory.py -timeplot logfile.pickle ts_ident
rand_seed determines which 1000 series random sample is taken from the record set. 
ts_ident is the identifier of the single series to view, in the 
format 'circ_id,ip_slug'.
@author: Julian Applebaum

@author: Shalisa Pattarawuttiwong 
	Last Edited: 08/04/14
		-modified doTimeplot to plot multiple line graphs  
"""

from scipy.stats import skew, pearsonr
from numpy import mean, std, median, linspace, correlate
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Rectangle
from sklearn.cluster import k_means
from pprint import pprint
from math import sqrt
from sequence_utils import trim_inactive_preprocess, flatten
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

def do_summarize(records):
	"""
	Display summary histograms for the series in records.
	@param records: the circuit records
	"""
	circ_len_aggr = []
	in_mean_cells_per_window_aggr = []
	in_min_cells_per_window_aggr = []
	in_max_cells_per_window_aggr = []
	in_median_cells_per_window_aggr = []
	in_stddev_cells_per_window_aggr = []
	in_inst_counts_aggr = []
	#unique_vals_aggr = []
	percent_active_aggr = []
	time_active_aggr = []
	out_mean_cells_per_window_aggr = []
	out_min_cells_per_window_aggr = []
	out_max_cells_per_window_aggr = []
	out_median_cells_per_window_aggr = []
	out_stddev_cells_per_window_aggr = []
	out_inst_counts_aggr = []

	for record in records:
		relays = record['relays']
		in_relays = [r[0] for r in relays]
		out_relays = [r[1] for r in relays]
		circ_len_aggr.append((record['destroy'] - record['create'])/1000.0)
		in_mean_cells_per_window_aggr.append(1.0*sum(in_relays)/len(in_relays))
		out_mean_cells_per_window_aggr.append(1.0*sum(out_relays)/len(out_relays))

		in_median_cells_per_window_aggr.append(median(in_relays))
		out_median_cells_per_window_aggr.append(median(out_relays))
		in_min_cells_per_window_aggr.append(min(in_relays))
		out_min_cells_per_window_aggr.append(min(out_relays))
		in_max_cells_per_window_aggr.append(max(in_relays))
		out_max_cells_per_window_aggr.append(max(out_relays))
		in_stddev_cells_per_window_aggr.append(std(in_relays))
		out_stddev_cells_per_window_aggr.append(std(out_relays))
		in_inst_counts_aggr += in_relays
		out_inst_counts_aggr += out_relays
		# unique_vals_aggr.append(len(set(filter(lambda o: o > 2, relays))))
		time_active = len(trim_inactive_preprocess(relays))

		percent_active_aggr.append(100.0*time_active/len(relays))

		# time_active_aggr.append(time_active)
	fig = plt.figure()
	summarize(in_max_cells_per_window_aggr, "Max IN")
	summarize(out_max_cells_per_window_aggr, "Max OUT")


	meansplot = fig.add_subplot(421)
	plt.title("Mean Cells/Window")
	plt.xlabel("Mean Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	meansplot.hist(in_mean_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='in')
	meansplot.hist(out_mean_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='out')

	cellsplot = fig.add_subplot(422)
	plt.title("Median Cells/Window")
	plt.xlabel("Median Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	cellsplot.hist(in_median_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='in')
	cellsplot.hist(out_median_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='out')

	minsplot = fig.add_subplot(423)
	plt.title("Min Cells/Window")
	plt.xlabel("Min Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	minsplot.hist(in_min_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='in')
	minsplot.hist(out_min_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='out')


	maxsplot = fig.add_subplot(424)
	plt.title("Max Cells/Window")
	plt.xlabel("Max Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	maxsplot.hist(in_max_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label="in")
	maxsplot.hist(out_max_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label="out")


	stddevsplot = fig.add_subplot(425)
	plt.title("Std Dev. of Cells/Window")
	plt.xlabel("Std Dev. of Cells/Window")
	plt.ylabel("Frequency")
	plt.yscale('log')
	stddevsplot.hist(in_stddev_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='in')
	stddevsplot.hist(out_stddev_cells_per_window_aggr, bins=N_HIST_BINS, alpha=0.5, label='out')

	cellsplot = fig.add_subplot(426)
	plt.title("Single Window Cell Count")
	plt.xlabel("Single Window Cell Count")
	plt.ylabel("Frequency")
	plt.yscale('log')
	cellsplot.hist(in_inst_counts_aggr, bins=N_HIST_BINS, alpha=0.5, label='in')
	cellsplot.hist(out_inst_counts_aggr, bins=N_HIST_BINS, alpha=0.5, label='out')


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

def do_horizon(records, window_size, ylim=None):
	"""
	Display a horizon plot for a size 1000 random sample of records
	@param records: the circuit records
	@param window_size: the size of the cell count windows
	"""
	sample = draw_sample(records)
	fig = plt.figure()
	fig.canvas.mpl_connect('pick_event', on_pick)
	ax = fig.add_subplot(2,2,1)
	plt.title("Inbound Horizon Plot (n=%i)" % len(sample))
	plt.xlabel("Window # (%i ms windows)" % window_size)
	plt.ylabel("Ingoing Relay Cells/Window")
	plt.grid(True)
	for record in sample:
		s = record['relays']
		series = [i[0] for i in s]
		# use fill_between to avoid some rendering bugs
		artist = ax.fill_between(range(0, len(series)), series, [0]*len(series),
			alpha=.2, color='black', edgecolor='none', picker=True)
		artist_ident_map[record['ident']] = artist

	ay = fig.add_subplot(2,2,3)
	plt.title("Outbound Horizon Plot (n=%i)" % len(sample))
	plt.xlabel("Window # (%i ms windows)" % window_size)
	plt.ylabel("Outgoing Relay Cells/Window")
	plt.grid(True)
	for record in sample:
		s = record['relays']
		series = [i[1] for i in s]
		# use fill_between to avoid some rendering bugs
		artist = ay.fill_between(range(0, len(series)), series, [0]*len(series),
			alpha=.2, color='black', edgecolor='none', picker=True)
		artist_ident_map[record['ident']] = artist

	fig.tight_layout()
	if ylim is not None:
		pylab.ylim([0, ylim])

def do_timeplot(records, window_size, ts_ident_list):
	"""
	Display a time plot and a correlogram for multiple time series
	@param records: the list of circuits records containing the series
	@param window_size: the size of the cell count windows
	@param ts_ident: the list of [(circ_id, ip_slug)]
				tuples identifying the series
	"""
	subplot_size = 421

	fig = plt.figure()

	# have to do this once first to be able to scale the subplots to the same scale
	rstr, cstr, ipstr = ts_ident_list[0].split(",")
	rstr = rstr.replace("(", "")
	cstr = cstr.replace(")", "")
	fig.canvas.set_window_title("%s-%i-%i-%i" % (rstr, int(cstr),
		int(ipstr), window_size))
	timeplot = fig.add_subplot(subplot_size)
	for record in records:
		if record['ident'] == ((rstr, int(cstr)), int(ipstr)):
			s = record['relays']
			in_series = [i[0] for i in s]
			out_series = [i[1] for i in s]
			plt.plot(in_series)
			plt.plot(out_series)
	subplot_size += 1

	for ident in ts_ident_list[1:]:
		rstr, cstr, ipstr = ident.split(",")
		rstr = rstr.replace("(","")
		cstr = cstr.replace(")","")
		fig.canvas.set_window_title("%s-%i-%i-%i" % (rstr, int(cstr), int(ipstr), window_size))

		timeplot1 = fig.add_subplot(subplot_size, sharex=timeplot, sharey=timeplot)
		# acorrplot = fig.add_subplot(122)
		for record in records:
			if record['ident'] == ((rstr, int(cstr)), int(ipstr)):
				plt.xlabel("Window # (%i ms windows)" % window_size)
				plt.ylabel("Ingoing Relay Cell Count")
				s = record['relays']
				in_series = [i[0] for i in s]

				# line graphs
				plt.plot(in_series)
				
				plt.xlabel("Window # (%i ms windows)" % window_size)
				plt.ylabel("Outgoing Relay Cell Count")
				out_series = [i[1] for i in s]

				# line graphs
				plt.plot(out_series)
				
			#	timeplot.fill_between(range(0, len(series)), series, [0]*len(series),
				#	color='grey')
				# acorr_plot(series, acorrplot)

		subplot_size += 1
	fig.text(0.5, 0.04, 'Window # (%i ms windows)'% window_size, ha='center', va='center')
	fig.text(0.06, 0.5, 'Outgoing Relay Cell Count', ha='center', va='center', rotation='vertical')

def do_colorplot(records, window_size, ax=None, ay=None, no_chrome=False,
	sample_size=1000):
	"""
	Display a color plots for a size 1000 random sample of records
	@param records: the circuit records
	@param window_size: the size of the cell count windows
	"""
	def rec_cmp(rec_1, rec_2):
		relays_1, relays_2 = rec_1['relays'], rec_2['relays']
		m_r1, m_r2= ((mean([i[0] for i in relays_1]) + 
			mean([i[1] for i in relays_1])), 
			(mean([i[0] for i in relays_2]) + 
			mean([i[1] for i in relays_2])))
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
	relay_series = [record['relays'] for record in sample]

	in_relay_series = []
	out_relay_series = []
	for r in relay_series:
		newTupIn = []
		newTupOut = []
		for tup in r:
			newTupIn.append(tup[0])
			newTupOut.append(tup[1])
		in_relay_series.append(newTupIn)
		out_relay_series.append(newTupOut)

	vmin = 0
	vmax = VMAX
	if ax is None:
		fig = plt.figure()
		fig.canvas.mpl_connect('pick_event', on_pick)
		ax = fig.add_subplot(221)
		ax.get_yaxis().set_ticks([])
	if not no_chrome:
		plt.title("Inbound Luminance Plot (n=%i)" % len(sample))
		plt.xlabel("Window # (%i ms windows)" % window_size)
		plt.ylabel("Client")
		# legend_rects = [Rectangle((0, 0), 1, 1, fc=c) for c in reversed(colors)]
		# legend_labels = ["%i-%i cells" % c for c in reversed(cluster_ranges)]
		# plt.legend(legend_rects, legend_labels, loc=4)
	n = 0
	for i in xrange(0, len(sample)):
		series = in_relay_series[i]
		ident = sample[i]['ident']
		artist = ax.scatter(range(0, len(series)), [n]*len(series),
			c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax,
			cmap=cm.coolwarm, picker=True)
		n += 2
		artist_ident_map[ident] = artist

	if ay is None:
		ay = fig.add_subplot(223)
		ay.get_yaxis().set_ticks([])
	if not no_chrome:
		plt.title("Outbound Luminance Plot (n=%i)" % len(sample))
		plt.xlabel("Window # (%i ms windows)" % window_size)
		plt.ylabel("Client")
		# legend_rects = [Rectangle((0, 0), 1, 1, fc=c) for c in reversed(colors)]
		# legend_labels = ["%i-%i cells" % c for c in reversed(cluster_ranges)]
		# plt.legend(legend_rects, legend_labels, loc=4)
	n = 0
	for i in xrange(0, len(sample)):
		series = out_relay_series[i]
		ident = sample[i]['ident']
		artist = ay.scatter(range(0, len(series)), [n]*len(series),
			c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax,
			cmap=cm.coolwarm, picker=True)
		n += 2
		artist_ident_map[ident] = artist

	fig.tight_layout()
	if not no_chrome:
		fig.subplots_adjust(right=1.0)
		cbar_ax = fig.add_axes([0.55, 0.15, 0.025, 0.7])
		fig.colorbar(artist, cax=cbar_ax)

if __name__ == "__main__":
	graphing_mode = sys.argv[1]
	inpath = sys.argv[2]
	if len(sys.argv) > 4: seed = int(sys.argv[3])
	else: seed = 0
	print "Random seed =", seed
	random.seed(seed)
	ts_ident_list = []
	with open(inpath) as data_file:
		print "Reading data..."
		data = cPickle.load(data_file)
	window_size, records = data['window_size'], data['records']
	if graphing_mode == "-timeplot":
		for arg in range(len(sys.argv)):
			if arg >= 5:
				ts_ident_list.append(sys.argv[arg])
	elif graphing_mode == "-agg-colorplots":
		k_val = int(sys.argv[4])
		records = filter(lambda r: r['ident'] == (k_val, k_val), records)
	print "%i series" % len(records)
	print "Graphing..."
	if graphing_mode == '-summarize':
		do_summarize(records)
	elif graphing_mode == '-horizon':
		do_horizon(records, window_size)
	elif graphing_mode == '-timeplot':
		do_timeplot(records, window_size, ts_ident_list)
	elif graphing_mode == '-colorplots':
		do_colorplot(records, window_size)
	elif graphing_mode == '-agg-colorplots':
		do_colorplot(records, window_size)
		do_horizon(records, window_size, MAX_OBS)
	else:
		print "ERROR: Invalid graphing mode selected"
	plt.show()
