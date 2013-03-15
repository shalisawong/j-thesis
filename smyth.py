"""
An implementation of Smyth 1997's HMM clustering algorithm. Currently
only supports time series data with 1-dimensional observations.

@author Julian Applebaum
"""

from ghmm import Float, GaussianDistribution, HMMFromMatrices, SequenceSet
from sklearn.cluster import k_means
from numpy import std, mean, array
from numpy import float as npfloat
from numpy import std
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

def train_hmm(pair):
	cluster, m = pair
	seqSet = toSequenceSet(cluster)
	hmm = getDefaultHMM(pair)
	hmm.baumWelch(seqSet)
	return str(hmm)

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
		emmision_distrs = pool.map(getEmissionDistribution, [([s], self.m) for s in S])
		hmms = map(hmmFromDistr, emmision_distrs)
		dmatrix = uniformMatrix(len(S), len(S))
		max_l = float('-inf')
		seqSet = toSequenceSet(S)

		print "Building distance matrix..."
		for j in xrange(0, N):
			for i in xrange(0, N):
				if (j > i):
					dmatrix[j][i] = 0
				else:
					si_mj = hmms[j].loglikelihood(seqSet[i])
					sj_mi = hmms[i].loglikelihood(seqSet[j])
					assert not isnan(si_mj)
					assert not isnan(sj_mi)
					sym = (si_mj + sj_mi)/2.0
					max_l = max(max_l, sym)
					dmatrix[j][i] = min(-1 * sym, MAX_DIST)

		print "Hierarchical clustering..."
		clusters = clusterFromDMatrix(S, self.k, dmatrix)
		print "Default HMMs for clusters..."
		print "Baum Welch reestimation (parallel)..."
		trained_hmms = pool.map(train_hmm, zip(clusters, [self.m]*len(clusters)))
		self.model = trained_hmms
		self.clusters = clusters

	def score(self, S_test):
		return self.model.loglikelihood(toSequenceSet(S_test))

	def get_params(self, deep):
		return { 'm': self.m, 'k': self.k }

	def set_params(self, **params):
		self.m = params['m']
		self.k = params['k']

# Run the experiment Smyth details
if __name__ == "__main__":
	inpath = sys.argv[1]
	outpath = sys.argv[2]
	with open(inpath) as datafile:
		with open(outpath, 'w') as clustfile:
			print "Loading data..."
			circuits = json.load(datafile)
			m = 6
			k = 4
			sequences = [circ['relays'] for circ in circuits]
			print "Clustering..."
			clust = HMMCluster(m, k)
			clust.fit(sequences)
			pprint(clust.model)
			json.dump(clustersToLists(clust.clusters), clustfile)
