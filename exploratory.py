from autotor import MultiLogFile, TimeSeries, DIR_IN, DIR_OUT
from scipy.stats import skew
from numpy import mean, std, correlate
import matplotlib.pyplot as plt
import sys

BUCKET_SIZE = 1000 # size, in milliseconds, of sampling buckets

def autocorrelate(values, lag=1):
	shifted = values[lag:-1]
	return correlate(values, shifted)[0]

def optimalLag(values, max_lag=10):
	optimal = 1
	best_corr = float('-inf')
	for lag in xrange(1, max_lag+1):
		corr = autocorrelate(values, lag)
		if corr > optimal:
			optimal = lag
			best_corr = corr

	return optimal

def summarize(values, name):
	border_len = len(name) + 8
	print "*" * border_len
	print "***", name, "***"
	print "Mean:", mean(values)
	print "Min:", min(values)
	print "Max:" , max(values)
	print "Std Dev:", std(values)
	print "Skewness:", skew(values)
	print "*" * border_len, "\n"

mf = MultiLogFile("/Users/julianapplebaum/Documents/Wesleyan/Thesis/"+
				  "data/clientlog-2013-02-05.log", DIR_OUT)

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
optimal_lag_aggr = []
all_cells_per_second = []

graphing_mode = sys.argv[1]

for circ in mf.circs.values():
	n_circs_total += 1
	time_series = TimeSeries(circ['times'])
	bucketized = time_series.bucketize(bucket_size=1000)
	circ_len = time_series.total_time()/1000

	if circ_len == 0:
		n_zero_len_circs += 1
	else:
		if max(bucketized) > 50:
			circ_len_aggr.append(circ_len)
			mean_cells_per_second_aggr.append(1.0*len(time_series.times)/
											  circ_len)
			min_cells_per_second_aggr.append(min(bucketized))
			max_cells_per_second_aggr.append(max(bucketized))
			stddev_cells_per_second_aggr.append(std(bucketized))
			optimal_lag = optimalLag(bucketized)
			optimal_lag_aggr.append(optimal_lag)

			if optimal_lag > 5:
				chosen_series.append(bucketized)

			for sample in bucketized:
				all_cells_per_second.append(sample)

n_chosen = len(chosen_series)
print n_circs_total, " circuits total"
print n_zero_len_circs, "0 second circuits"
print n_chosen, "time series selected for analysis"

summarize(mean_cells_per_second_aggr, "Mean Cells/Second")
summarize(circ_len_aggr, "Circuit Length (seconds)")

if graphing_mode == '-summarize':
	lenplot = plt.subplot(411)
	plt.title("Circuit Time Frequencies")
	lenplot.hist(circ_len_aggr, bins=100)

	meansplot = plt.subplot(412)
	plt.title("Mean Cell/Second Frequencies")
	meansplot.hist(mean_cells_per_second_aggr, bins=100)

	lagsplot = plt.subplot(413)
	plt.title("Optimal Lag Frequencies")
	lagsplot.hist(optimal_lag_aggr, bins=100)

	cellsplot = plt.subplot(414)
	plt.title("Instantaneous Cells/Second Frequencies")
	cellsplot.hist(all_cells_per_second, bins=20)
elif graphing_mode == '-timeplots':
	plt.title("Time Plots (n=%i)" % n_chosen)

	for series in chosen_series:
		plt.plot(series)
else:
	print "ERROR: No graphing mode selected"

plt.show()
