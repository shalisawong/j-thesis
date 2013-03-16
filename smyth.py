"""
An implementation of Smyth 1997's HMM clustering algorithm. Currently
only supports time series data with 1-dimensional observations.

@author Julian Applebaum
"""

from ghmm import Float, GaussianDistribution, HMMFromMatrices, SequenceSet
from sklearn.cluster import k_means
from sklearn.metrics.pairwise import pairwise_distances
from numpy import std, mean, array
from numpy import float as npfloat
from scipy.spatial.distance import squareform
from sample_gen import smyth_example, three_hmm
from matrix_utils import uniformMatrix
from cluster_utils import clusterFromDMatrix
from sequence_utils import *
from hmm_utils import compositeHMM
from pprint import pprint
from math import isnan
from multiprocessing import Pool
import sys, json

EPSILON = .00001
MAX_DIST = 10**9

# These functions really belong as member functions of HMMCluster,
# but we need to leave them at the module level for multiprocessing.

def getEmissionDistribution(pair):
	"""
	Partition the individual observations in S into m clusters,
	then calculate the mean and standard deviation of each one.
	Returns an emission distribution for use with the Gaussian HMM.
	"""
	S, m = pair
	flattened = []
	for s in S:
		for o in s:
			flattened.append(o)

	vectorized = [[o] for o in flattened]
	m_prime = min(m, len(flattened))
	centroids, labels, inertia = k_means(vectorized, m_prime)

	clusters = [[] for i in xrange(0, m_prime)]
	for i in xrange(0, len(flattened)):
		clusters[labels[i]].append(flattened[i])

	B = []
	for cluster in clusters:
		if len(cluster) > 0:
			mu = mean(cluster)
			stddev = std(cluster) or EPSILON # The Gaussian is undefined for
			B.append((mu, stddev))			 # standard deviation of 0, which
										 	 # can happen on uniform data
	return B

def getDefaultHMM(pair):
		"""
		Initialize a m state HMM with emission domain sigma using
		Smyth's "default" method.
		"""
		cluster, m = pair
		B = getEmissionDistribution(pair)
		return hmmFromDistr(B)

def hmmFromDistr(B):
	m = len(B)
	A = [[1.0/m] * m] * m
	distr = GaussianDistribution(None)
	pi = [1.0/m] * m
	return HMMFromMatrices(Float(), distr, A, B, pi)

def symDistance(items):
	pair1, pair2 = items
	cluster1, distr1 = pair1
	cluster2, distr2 = pair2
	hmm1 = hmmFromDistr(distr1)
	hmm2 = hmmFromDistr(distr2)
	s1_m2 = hmm2.loglikelihood(toSequenceSet(cluster1))
	s2_m1 = hmm1.loglikelihood(toSequenceSet(cluster2))
	sym = (s1_m2 + s2_m1)/2.0
	return min(-1 * sym, MAX_DIST)

def trainHMM(pair):
	cluster, m = pair
	seqSet = toSequenceSet(cluster)
	hmm = getDefaultHMM(pair)
	hmm.baumWelch(seqSet)
	return str(hmm)

def seqModelPair(pair):
	return (pair[0], getEmissionDistribution(pair))

class HMMCluster():
	def __init__(self, m, k):
		self.m = m
		self.k = k

	def fit(self, S):
		"""
		Create a m*k state HMM mixture modeling the sequences in S.
		The HMM is returned as well as the clustering result used for
		the mixture components.
		"""
		pool = Pool()
		N = len(S)
		print "Generating default HMMs (parallel)..."
		seqmodel_pairs = pool.map(seqModelPair, [([s], self.m) for s in S])
		dist_pairs = []
		print "Computing distance matrix (parallel)..."
		for r in xrange(0, N):
			for c in xrange(1+r, N):
				dist_pairs.append((seqmodel_pairs[r], seqmodel_pairs[c]))
		condensed = pool.map(symDistance, dist_pairs)
		square = squareform(condensed)
		for c in xrange(0, N):
			for r in xrange(1+c, N):
				square[r][c] = 0

		print square

		print "Hierarchical clustering (serial)..."
		clusters = clusterFromDMatrix(S, self.k, square)
		print "Training HMMs on clusters (parallel)..."
		trained_hmms = pool.map(trainHMM, zip(clusters, [self.m]*len(clusters)))
		self.model = trained_hmms
		self.clusters = clusters

	def score(self, S_test):
		return self.model.loglikelihood(seqSetToListequenceSet(S_test))

	def get_params(self, deep):
		return { 'm': self.m, 'k': self.k }

	def set_params(self, **params):
		self.m = params['m']
		self.k = params['k']

if __name__ == "__main__":
	inpath = sys.argv[1]
	m = int(sys.argv[2])
	k = int(sys.argv[3])
	if inpath == "-smythex":
		print "Generating synthetic data..."
		sequences = seqSetToList(smyth_example(n=20))
	else:
		with open(inpath) as datafile:
			print "Loading data..."
			circuits = json.load(datafile)
			sequences = [circ['relays'] for circ in circuits][:100]

	print "Clustering..."
	clust = HMMCluster(m, k)
	clust.fit(sequences)
	for hmm in clust.model:
		print hmm
