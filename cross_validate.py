"""
An implementation of Smyth 1997's Monte Carlo cross validation procedure

@author Julian Applebaum
"""

import smyth
from random import shuffle, seed
from pprint import pprint
from ghmm import SequenceSet, Float
from sample_gen import smyth_example
from numpy import mean, std
from math import exp
from multiprocessing import pool

N_SAMPLES = 20
K_MAX = 6
BETA = .5
M = 2

def randPartition(S, beta):
	"""
	Randomly partion S into two SequenceSets A and B s.t.
	len(A) = len(S) * beta, len(B) = len(S) * (1-beta)
	"""
	S_list = list(S)
	idx = int(BETA * len(S_list))
	shuffle(S_list)
	return (SequenceSet(Float(), S_list[:idx]),
			SequenceSet(Float(), S_list[idx:]))

def computeLikelihood(S_test, S_train, m, k):
	hmm, clustering = smyth.hmmCluster(S_train, m, k, True)
	return hmm.loglikelihood(S_test)

if __name__ == "__main__":
	seed(20)
	S = smyth_example(n=5)
	k_likelihoods = {}

	for i in xrange(0, N_SAMPLES):
		print "Sample #%i" % (i+1)
		S_test, S_train = randPartition(S, BETA)

		for k in xrange(1, K_MAX+1):
			if k not in k_likelihoods:
				k_likelihoods[k] = []

			likelihood = computeLikelihood(S_test, S_train, M, k)
			k_likelihoods[k].append(likelihood)

	denom = sum([mean(ls) for ls in k_likelihoods.values()])

	for k, ls in k_likelihoods.items():
		# print "max likelihood for k=%i: %f" % (k, max(ls))
		# print "min likelihood for k=%i: %f" % (k, min(ls))
		print "mean likelihood for k=%i: %f" % (k, mean(ls)/denom)
		print "std dev for k=%i: %f\n" % (k, std(ls))

