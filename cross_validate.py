"""
An implementation of Smyth 1997's Monte Carlo cross validation procedure

@author Julian Applebaum
"""

from smyth import HMMCluster
from pprint import pprint
from sample_gen import smyth_example, three_hmm
from numpy import mean, std
from sklearn.cross_validation import ShuffleSplit, cross_val_score

N_SPLITS = 20
K_MAX = 4
M_MAX = 4
BETA = .5

if __name__ == "__main__":
	S = three_hmm()
	cv = ShuffleSplit(len(S), N_SPLITS, BETA, random_state=0)

	for k in xrange(1, K_MAX+1):
		for m in xrange(2, M_MAX+1):
			model = HMMCluster(m, k)
			score = cross_val_score(model, S, cv=cv, n_jobs=-1)
			print "k = %i, m = %i --> %f, %f, %f" % (k, m, mean(score),
				std(score), max(score))
