import matplotlib.pyplot as plt
from numpy import mean, std, median
from scipy import stats
from pprint import pprint
import sys, cPickle

def conf_inter(sigma, n):
	return 2*stats.t.isf([.05], n-1)[0]*sigma

def get_diff(i, means):
	return 100*(means[i]-means[i-1])/means[i-1]

def get_stats(likelihoods, means, mins, maxes, confs):
	means.append(mean(likelihoods))
	mins.append(min(likelihoods))
	maxes.append(max(likelihoods))
	sigma = std(likelihoods)
	confs.append(conf_inter(sigma, len(likelihoods)))

if __name__ == "__main__":
	results_path = sys.argv[1]
	with open(results_path) as results_file:
		results = cPickle.load(results_file)
		ks = sorted(set(map(lambda r: r[0], results)))
		ms = sorted(set(map(lambda r: r[1], results)))
		k_likelihoods = dict([(k, []) for k in ks])
		m_likelihoods = dict([(m, []) for m in ms])
		k_means, k_confs = [], []
		m_means, m_confs = [], []
		k_mins, k_maxes = [], []
		m_mins, m_maxes = [], []
		k_diffs, m_diffs = [], []
		best_m_likelihoods = dict([(k, []) for k in ks])
		best_m_means, best_m_confs = [], []
		best_m_mins, best_m_maxes = [], []
		for k, target_m, rand_seed, likelihood in results:
			k_likelihoods[k].append(likelihood)
			m_likelihoods[target_m].append(likelihood)
		for k in ks:
			likelihoods = k_likelihoods[k]
			get_stats(likelihoods, k_means, k_mins, k_maxes, k_confs)
		for m in ms:
			likelihoods = m_likelihoods[m]
			get_stats(likelihoods, m_means, m_mins, m_maxes, m_confs)
		for i in xrange(1, len(k_means)):
			diff = get_diff(i, k_means)
			k_diffs.append(diff)
		for i in xrange(1, len(m_means)):
			diff = get_diff(i, m_means)
			m_diffs.append(diff)
		best_m = min(ms) + m_means.index(max(m_means))
		for k, target_m, rand_seed, likelihood in results:
			if target_m == best_m: best_m_likelihoods[k].append(likelihood)
		for k in ks:
			likelihoods = best_m_likelihoods[k]
			get_stats(likelihoods, best_m_means, best_m_mins, best_m_maxes,
				best_m_confs)
		best_k = min(ks) + best_m_means.index(max(best_m_means))

		print "***********************"
		print "*** Best Parameters ***"
		print "***    k=%i, m=%i    ***" % (best_k, best_m)
		print "***********************"

		fig = plt.figure()
		kplot = fig.add_subplot(221)
		plt.title("Mean Log Likelihood vs. k")
		plt.xlabel("k")
		plt.ylabel("Log Likelihood")
		kplot.bar(ks, k_mins, 1, color='r')
		kplot.bar(ks, k_means, 1, color='y', yerr=k_confs)
		kplot.bar(ks, k_maxes, 1, color='g')

		mplot = fig.add_subplot(222)
		plt.title("Mean Log Likelihood vs. Target m")
		plt.xlabel("Target m")
		plt.ylabel("Log Likelihood")
		mplot.bar(ms, m_mins, 1, color='r')
		mplot.bar(ms, m_means, 1, color='y', yerr=m_confs)
		mplot.bar(ms, m_maxes, 1, color='g')

		kdiffplot = fig.add_subplot(223)
		plt.title("% Change in Log Likelihood vs. k")
		plt.xlabel("k")
		plt.ylabel("% change")
		kdiffplot.bar(ks[1:], k_diffs, 1, color='y')

		bestmplot = fig.add_subplot(224)
		plt.title("Mean Log Likelihood vs. k (Target m=%i)" % best_m)
		plt.xlabel("k")
		plt.ylabel("Log Likelilihood")
		bestmplot.bar(ks, best_m_means, 1, color='y', yerr=best_m_confs)

		fig.tight_layout()
		plt.show()
