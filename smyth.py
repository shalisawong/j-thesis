"""
An implementation of Smyth 1997's HMM clustering algorithm. Currently
only supports time series data with 1-dimensional observations.

@author Julian Applebaum
"""

from ghmm import Float, GaussianDistribution, HMMFromMatrices, SequenceSet
from sklearn.cluster import k_means
from numpy import std, mean, array
from numpy import float as npfloat
from sample_gen import smyth_example
from matrix_utils import uniformMatrix
from cluster_utils import clusterFromDMatrix
from sequence_utils import singleton, toSequence, toSequenceSet
from hmm_utils import compositeHMM
from pprint import pprint

EPSILON = .00001

class HMMCluster():
	def __init__(self, m, k):
		self.m = m
		self.k = k

	def fit(self, S_arr):
		"""
		Create a m*k state HMM mixture modeling the sequences in S.
		The HMM is returned as well as the clustering result used for
		the mixture components.
		"""
		S = toSequenceSet(S_arr)
		N = len(S)
		hmms = [self._getDefaultHMM(singleton(s), self.m, Float()) for s in S]
		dmatrix = uniformMatrix(len(S), len(S))
		max_l = float('-inf')

		for j in xrange(0, N):
			for i in xrange(0, N):
				if (j > i):
					dmatrix[j][i] = 0
				else:
					si_mj = hmms[j].loglikelihood(S[i])
					sj_mi = hmms[i].loglikelihood(S[j])
					sym = (si_mj + sj_mi)/2.0
					max_l = max(max_l, sym)
					dmatrix[j][i] = -1 * sym

		clusters = clusterFromDMatrix(S, self.k, dmatrix)
		new_hmms = [self._getDefaultHMM(c, self.m, Float()) for c in clusters]
		weights = [1.0*len(c)/N for c in clusters]
		composite = compositeHMM(new_hmms, weights)
		composite.baumWelch(S)
		self.model = composite
		self.clusters = clusters
		#print self.model

	def score(self, S_test):
		return self.model.loglikelihood(toSequenceSet(S_test))

	def get_params(self, deep):
		return { 'm': self.m, 'k': self.k }

	def set_params(self, **params):
		self.m = params['m']
		self.k = params['k']

	def _getEmissionDistribution(self, S, m):
		"""
		Partition the individual observations in S into m clusters,
		then calculate the mean and standard deviation of each one.
		Returns an emission distribution for use with the Gaussian HMM.
		"""
		flattened = []
		for s in S:
			for o in s:
				flattened.append(o)

		vectorized = [[o] for o in flattened]
		centroids, labels, inertia = k_means(vectorized, m)

		clusters = [[] for i in xrange(0, m)]
		for i in xrange(0, len(flattened)):
			clusters[labels[i]].append(flattened[i])

		B = []
		for cluster in clusters:
			mu = mean(cluster)
			stddev = std(cluster) or EPSILON # The Gaussian is undefined for
			B.append((mu, stddev))			 # standard deviation of 0, which
											 # can happen on uniform data
		return B

	def _getDefaultHMM(self, S, m, sigma):
		"""
		Initialize a m state HMM with emission domain sigma using
		Smyth's "default" method.
		"""
		A = [[1.0/m] * m] * m
		B = self._getEmissionDistribution(S, m)
		distr = GaussianDistribution(None)
		pi = [1.0/m] * m
		return HMMFromMatrices(sigma, distr, A, B, pi)


# Run the experiment Smyth details
if __name__ == "__main__":
  	print "Creating sample data..."
  	S = smyth_example()
  	print "Building model...\n"
	model = HMMCluster(2, 2)
	model.fit(S)
	print model.model
