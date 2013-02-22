from scipy.stats import skew, pearsonr
from numpy import mean, std, linspace
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib import cm
import sys, json

# provides some operations on lists convenient for doing time series analysis
class TimeSeries(object):
    def __init__(self,data=[],prune=0):
        # prune lets us get rid of any extraneous values
        self.times = data[prune:]
    # divide into buckets so we can do levine correlation
    # bucket size is in milliseconds
    def bucketize(self,bucket_size=1000,adj=True):
        adj_times = [t - self.times[0] for t in self.times]
        bucketized = [t/bucket_size for t in adj_times]
        buckets = sorted(bucketized)
        ts = []
        i = 0
        for b in range(buckets[-1]+1):
            ts.append(0)
            while i < len(buckets) and b == buckets[i]:
                i += 1
                ts[b] += 1
        if adj:
            return ts
        else:
            return ([0] * int((self.times[0]-1266390000000)/bucket_size)) + ts
    def intervals(self):
        return [self.times[i] - self.times[i-1] for i in range(1,len(self.times))]
    def total_time(self):
        return self.times[-1] - self.times[0]
    def __len__(self):
        return len(self.times)

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

def autocorrelate(values, lag=1):
	shifted = values[0:len(values)-1-lag]
	values_cutoff = values[lag:len(values)-1]
	# print values
	# print shifted
	# print values_cutoff
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
if len(sys.argv) > 4:
	censor = int(sys.argv[4])

with open(filepath) as data_file:
	circuits = json.load(data_file)

	n_circs_total = 0
	n_zero_len_circs = 0
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
		time_series = TimeSeries(circ)
		bucketized = time_series.bucketize(bucket_size=bucket_size)
		circ_len = time_series.total_time()/bucket_size

		if circ_len == 0:
			n_zero_len_circs += 1
		else:
			if graphing_mode == '-summarize':
				circ_len_aggr.append(circ_len)
				mean_cells_per_second_aggr.append(1.0*len(time_series.times)/
												  circ_len)
				min_cells_per_second_aggr.append(min(bucketized))
				max_cells_per_second_aggr.append(max(bucketized))
				stddev_cells_per_second_aggr.append(std(bucketized))
				top_lags = topNLags(bucketized, 3)

				if len(top_lags) == 3:
					optimal1_lag_aggr.append(top_lags[0])
					optimal2_lag_aggr.append(top_lags[1])
					optimal3_lag_aggr.append(top_lags[2])

			for sample in bucketized:
				all_cells_per_second.append(sample)

			chosen_series.append(bucketized)

	chosen_series.sort(cmp=seq_cmp)
	n_chosen = len(chosen_series)
	print n_circs_total, "circuits total"
	print n_zero_len_circs, "0 second circuits"
	print n_chosen, "time series selected for analysis"

	if graphing_mode == '-summarize':
		summarize(mean_cells_per_second_aggr, "Mean Cells/Second")
		summarize(circ_len_aggr, "Circuit Length (seconds)")

		lenplot = plt.subplot(321)
		plt.title("Circuit Time Frequencies")
		lenplot.hist(circ_len_aggr, bins=100)

		meansplot = plt.subplot(322)
		plt.title("Mean Cell/Second Frequencies")
		meansplot.hist(max_cells_per_second_aggr, bins=100)

		cellsplot = plt.subplot(323)
		plt.title("Instantaneous Cells/Second Frequencies")
		cellsplot.hist(all_cells_per_second, bins=20)

		lagsplot1 = plt.subplot(324)
		plt.title("Optimal Lag Frequencies")
		lagsplot1.hist(optimal1_lag_aggr, bins=200)

		lagsplot2 = plt.subplot(325)
		plt.title("2nd Best Lag Frequencies")
		lagsplot2.hist(optimal2_lag_aggr, bins=200)

		lagsplot3 = plt.subplot(326)
		plt.title("3rd Best Lag Frequencies")
		lagsplot3.hist(optimal3_lag_aggr, bins=200)

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
