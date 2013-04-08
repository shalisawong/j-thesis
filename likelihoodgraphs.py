import matplotlib.pyplot as plt
from numpy import mean, std
from scipy import stats
from pprint import pprint
import sys, cPickle

def conf_inter(sigma, n):
	return 2*stats.t.isf([.75], n-1)[0]*sigma

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
		for k, target_m, rand_seed, likelihood in results:
			k_likelihoods[k].append(likelihood)
			m_likelihoods[target_m].append(likelihood)
		for k in ks:
			likelihoods = k_likelihoods[k]
			k_means.append(mean(likelihoods))
			sigma = std(likelihoods)
			k_confs.append(conf_inter(sigma, len(likelihoods)))
		for m in ms:
			likelihoods = m_likelihoods[m]
			m_means.append(mean(likelihoods))
			sigma = std(likelihoods)
			m_confs.append(conf_inter(sigma, len(likelihoods)))

		print stats.f_oneway(*k_likelihoods.values())
		print stats.f_oneway(*m_likelihoods.values())

		fig = plt.figure()
		kplot = fig.add_subplot(121)
		plt.title("Mean Log Likelihood vs. k")
		plt.xlabel("k")
		plt.ylabel("Log Likelihood")
		kplot.bar(ks, k_means, 1, color='y', yerr=k_confs)

		mplot = fig.add_subplot(122)
		plt.title("Mean Log Likelihood vs. Target m")
		plt.xlabel("Target m")
		plt.ylabel("Log Likelihood")
		mplot.bar(ms, m_means, 1, color='y', yerr=m_confs)

		fig.tight_layout()
		plt.show()
