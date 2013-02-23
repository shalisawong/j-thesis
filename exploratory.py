from scipy.stats import skew, pearsonr
from numpy import mean, std, linspace
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib import cm
from pprint import pprint
import sys, json

cdict = {'red': ((0., 1, 1),
                 (0.05, 1, 1),
                 (0.11, 0, 0),
                 (0.66, 1, 1),
                 (0.89, 1, 1),
                 (1, 0.5, 0.5)),
         'green': ((0., 1, 1),
                   (0.05, 1, 1),
                   (0.11, 0, 0),
                   (0.375, 1, 1),
                   (0.64, 1, 1),
                   (0.91, 0, 0),
                   (1, 0, 0)),
         'blue': ((0., 1, 1),
                  (0.05, 1, 1),
                  (0.11, 1, 1),
                  (0.34, 1, 1),
                  (0.65, 0, 0),
                  (1, 0, 0))}

my_cmap = LinearSegmentedColormap('my_colormap', cdict, 256)

def bucketize(record, bucket_size):
	start = record['create']
	end = record['destroy']
	relays = record['relays']
	circ_len = end - start
	adj_times = [t - start for t in relays]
	first_relay = adj_times[0]
	last_relay = adj_times[-1]
	bucketed = []
	window_end = bucket_size

	# pad with 0 buckets until we see relay cells
	while window_end < first_relay:
		bucketed.append(0)
		window_end += bucket_size

	n_cells = 0
	cur_time = 0

	# bucketize relay cells
	for cur_time in adj_times:
		if cur_time <= window_end:
			n_cells += 1
		else:
			bucketed.append(n_cells)
			window_end += bucket_size
			n_cells = 1

	# special case if all relay cells occur before our first window end
	if cur_time < window_end:
		bucketed.append(n_cells)

	# pad with 0 buckets until we reach the end of the series
	# while window_end < end:
	# 	bucketed.append(0)
	# 	window_end += bucket_size

	if len(bucketed) == 0:
		pprint(adj_times)
		print circ_len/1000
		exit()

	return bucketed

def autocorrelate(values, lag=1):
	shifted = values[0:len(values)-1-lag]
	values_cutoff = values[lag:len(values)-1]
	return pearsonr(values_cutoff, shifted)

def topNLags(values, n):
	optimal = 1
	lags_map = {}
	for lag in xrange(1, len(values)/4):
		corr = autocorrelate(values, lag)
		lags_map[corr] = lag

	corrs_sorted = sorted(lags_map.keys(), reverse=True)
	n_corrs = min(len(corrs_sorted), n)
	return [lags_map[corrs_sorted[i]] for i in xrange(0, n_corrs)]

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

graphing_mode = sys.argv[1]
filepath = sys.argv[2]
bucket_size = int(sys.argv[3])
censor = None
if len(sys.argv) > 5:
	censor = int(sys.argv[5])

with open(filepath) as data_file:
	circuits = json.load(data_file)

	n_circs_total = 0
	chosen_series = []

	# lists of descriptive statistics for individual series
	circ_len_aggr = []
	mean_cells_per_second_aggr = []
	min_cells_per_second_aggr = []
	max_cells_per_second_aggr = []
	stddev_cells_per_second_aggr = []
	skew_cells_per_second_agrr = []
	optimal1_lag_aggr = []
	optimal2_lag_aggr = []
	optimal3_lag_aggr = []
	all_cells_per_second = []

	for circ in circuits:
		n_circs_total += 1
		bucketized = bucketize(circ, bucket_size)
		circ_len = 1.0*(circ['destroy'] - circ['create'])

		if len(bucketized) > 0:
			if graphing_mode == '-summarize':
				circ_len_aggr.append(circ_len/1000)
				mean_cells_per_second_aggr.append(1.0*sum(bucketized)/circ_len)
				min_cells_per_second_aggr.append(min(bucketized))
				max_cells_per_second_aggr.append(max(bucketized))
				stddev_cells_per_second_aggr.append(std(bucketized))
				# top_lags = topNLags(bucketized, 3)

				# if len(top_lags) == 3:
				# 	optimal1_lag_aggr.append(top_lags[0])
				# 	optimal2_lag_aggr.append(top_lags[1])
				# 	optimal3_lag_aggr.append(top_lags[2])

			for sample in bucketized:
				all_cells_per_second.append(sample)

			chosen_series.append(bucketized)

	chosen_series.sort(cmp=seq_cmp)
	n_chosen = len(chosen_series)
	print n_circs_total, "circuits total"
	# print n_chosen, "time series selected for analysis"

	if graphing_mode == '-summarize':
		summarize(mean_cells_per_second_aggr, "Mean Cells/Second")
		summarize(circ_len_aggr, "Circuit Length (seconds)")

		lenplot = plt.subplot(311)
		plt.title("Circuit Time Frequencies")
		lenplot.hist(circ_len_aggr, bins=100)

		meansplot = plt.subplot(312)
		plt.title("Mean Cell/Second Frequencies")
		meansplot.hist(max_cells_per_second_aggr, bins=100)

		cellsplot = plt.subplot(313)
		plt.title("Instantaneous Cells/Second Frequencies")
		cellsplot.hist(all_cells_per_second, bins=100)

		# lagsplot1 = plt.subplot(324)
		# plt.title("Optimal Lag Frequencies")
		# lagsplot1.hist(optimal1_lag_aggr, bins=200)

		# lagsplot2 = plt.subplot(325)
		# plt.title("2nd Best Lag Frequencies")
		# lagsplot2.hist(optimal2_lag_aggr, bins=200)

		# lagsplot3 = plt.subplot(326)
		# plt.title("3rd Best Lag Frequencies")
		# lagsplot3.hist(optimal3_lag_aggr, bins=200)

	elif graphing_mode == '-timeplots':
		plt.title("Time Plots (n=%i)" % n_chosen)
		plt.grid(True)

		for series in chosen_series:
			plt.fill(series, alpha=.1, color='red')
	elif graphing_mode == '-colorplots':
		n = 1
		vmin = 0
		vmax = censor or max(all_cells_per_second)

		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.patch.set_facecolor('black')

		for series in chosen_series:
			scat = ax.scatter(range(0, len(series)), [n]*len(series),
				c=series, marker="s", edgecolors='none', vmin=vmin, vmax=vmax)
			n += 1

			if n == len(chosen_series)-1:
				plt.colorbar(scat)

	elif graphing_mode == '-autocorrs':
		vmin = -1
		vmax = 1
		i = 1

		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.patch.set_facecolor('black')
		did_bar = False

		for series in chosen_series:
			lags = []
			correlations = []
			for lag in xrange(1, len(series)/4):
				correlation = autocorrelate(series, lag)[0]
				if not isnan(correlation):
					lags.append(lag)
					correlations.append(correlation)

			if len(lags) > 0:
				scat = ax.scatter(lags, [i]*len(lags), c=correlations, marker="s",
					edgecolors='none', vmin=vmin, vmax=vmax)
				i += 1
				if not did_bar:
					plt.colorbar(scat)
					did_bar = True
	else:
		print "ERROR: No graphing mode selected"

	plt.show()
