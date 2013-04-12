from numpy import mean, std, median, meshgrid
from matplotlib import cm
from scipy import stats
from pprint import pprint
from matrix_utils import uniformMatrix
import matplotlib.pyplot as plt
import sys, cPickle

# Ignore very high ks when computing the best m since they're likely
# to be overfitted.
MAX_K = 20

def conf_inter(sigma, n):
	return 2*stats.t.isf([.05], n-1)[0]*sigma

def get_diff(i, means):
	return 100*(means[i]-means[i-1])/means[i-1]

if __name__ == "__main__":
	results_path = sys.argv[1]
	mode = sys.argv[2]
	with open(results_path) as results_file:
		results = cPickle.load(results_file)
		ks = sorted(set(map(lambda r: r[0], results)))
		ms = sorted(set(map(lambda r: r[1], results)))
		n_trials = len(set(map(lambda r: r[2], results)))
		km_means, km_trials = {}, {}
		sfc_zs = uniformMatrix(len(ms), len(ks))
		best_mean = float("-inf")
		global_best = float("-inf")
		best_m, best_k = None, None
		best_m_means, best_m_confs = [], []
		k_diffs = []
		for k in ks:
			for m in ms:
				km_means[(k, m)] = 0
				km_trials[(k, m)] = []
		for k, target_m, rand_seed, likelihood in results:
			km_means[(k, target_m)] += likelihood/n_trials
			km_trials[(k, target_m)].append(likelihood)
		for k in ks:
			for m in ms:
				mean_l = km_means[(k, m)]
				sfc_zs[m-min(ms),k-min(ks)] = mean_l
				if mean_l > best_mean and k == 7:
					best_mean = mean_l
					best_k = k
					best_m = m
				global_best = max(mean_l, global_best)
		for k in ks:
			trials = km_trials[(k, best_m)]
			best_m_means.append(mean(trials))
			sigma = std(trials)
			best_m_confs.append(conf_inter(sigma, len(trials)))
		for i in xrange(1, len(best_m_means)):
			k_diffs.append(get_diff(i, best_m_means))
		print "*******************"
		print "*** Best Parameters"
		print "*** k=%i, m=%i" % (best_k, best_m)
		print "*** (%i trials)" % n_trials
		print "*** Local best = %f" % best_mean
		print "*** Global best = %f" % global_best
		print "*** %% difference = %f" % ((best_mean - global_best)/global_best)
		print "*******************"
		fig = plt.figure()
		if mode == "-flat":
			bestmplot = fig.add_subplot(211)
			plt.title("Mean Log Likelihood vs. k (Target m=%i)" % best_m)
			plt.xlabel("k")
			plt.ylabel("Log Likelilihood")
			bestmplot.bar(ks, best_m_means, 1, color='y', yerr=best_m_confs)
			# bestmplot.plot(ks, best_m_means)
			kdiffplot = fig.add_subplot(212)
			plt.title("%% Change in Log Likelihood vs. k (Target m=%i)" % best_m)
			plt.xlabel("k")
			plt.ylabel("% change")
			kdiffplot.bar(ks[1:], k_diffs, 1, color='y')
			fig.tight_layout()
		elif mode == "-surface":
			ax = fig.add_subplot(111)
			plt.title("Mean Log Likelihood vs. k and m (22 trials)")
			plt.xlabel("k")
			plt.ylabel("m")
			im = plt.imshow(sfc_zs, extent=[min(ks), max(ks), max(ms), min(ms)],
				cmap=cm.coolwarm)
			plt.xticks(filter(lambda k: k%5==0, ks))
			fig.colorbar(im, shrink=.5, aspect=10)
			ax.grid()
		plt.show()
