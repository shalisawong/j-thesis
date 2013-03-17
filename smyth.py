"""
An multithreaded implementation of Smyth 1997's HMM clustering algorithm
for 1-dimensional time series data.
@author Julian Applebaum
"""

from ghmm import Float, GaussianDistribution, HMMFromMatrices, SequenceSet
from sklearn.cluster import k_means
from fastcluster import linkage
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import squareform
from numpy import std, mean, array
from numpy import float as npfloat
from sample_gen import smyth_example
from matrix_utils import uniformMatrix
from cluster_utils import partition
from sequence_utils import *
from hmm_utils import compositeTriple, hmmToTriple, tripleToHMM
from pprint import pprint
from math import isnan
from multiprocessing import Pool
import sys, json, pickle

EPSILON = .00001
MAX_DIST = 10**9

# These functions really belong as methods of HMMCluster or lambdas,
# but we need to leave them at the module level for multiprocessing.

def getEmissionDistribution(pair):
	"""
	Given a pair (S: list of sequences, m: int), get the emission
	distribution for Smyth's "default" HMM. m is an upper bound on the
	number of states -- if we can only produce m' nonempty clusters (eg.
	given a cluster of sequences likes [0, 1, 0, 1, .... 0, 1]), then the
	distribution for a m' state HMM is returned.

	@param pair: A tuple of the form (S: list of sequences, m: int)
	@return: The corresponding emission distribution encoded as a list
			 of (mu, stddev) pairs
	"""
	S, m = pair
	combined = flatten([[o] for o in s] for s in S)
	m_prime = min(m, len(combined))
	centroids, labels, inertia = k_means(combined, m_prime, init='k-means++')
	clusters = partition(combined, m_prime, labels)
	B = []
	for cluster in clusters:
		if len(cluster) > 0:
			mu = mean(cluster)
			stddev = std(cluster) or EPSILON # The Gaussian is undefined for
			B.append((mu, stddev))			 # standard deviation of 0, which
	return B								 # can happen on uniform data

def getDefaultHMM(pair):
	"""
	Initialize a m state Gaussian emission HMM using Smyth's "default" method.

	@param pair: A tuple of the form (S: list of sequences, m: int)
	@return: The HMM as as ghmm.GaussianEmmisionHMM.
	"""
	cluster, m = pair
	B = getEmissionDistribution(pair)
	return defaultHMMFromDistr(B)

def defaultHMMFromDistr(B):
	"""
	Given an emission distribution from getEmissionDistribution, fill
	in the A and pi matrices for Smyth's default HMM. We can do this because,
	since A and pi are both uniform, they can be determined just from the length
	of B.

	@param B: An emission distribution encoded as a list of (mu, stddev) pairs
	@return: A ghmm.GaussianEmmisionHMM with uniform A and pi, and emission
			 distribution B.
	"""
	m = len(B)
	A = [[1.0/m] * m] * m
	distr = GaussianDistribution(None)
	pi = [1.0/m] * m
	return HMMFromMatrices(Float(), distr, A, B, pi)

def symDistance(items):
	"""
	Calculate Rabiner's symmetrized distance measure between two sequences
	given their corresponding "default" models.

	@param items: A tuple of the form:
					((seq1, distr1), (seq2, distr2))
				  where seq1 and seq2 are singleton lists of emission sequences,
				  and distr1, distr2 are the corresponding emission distributions
				  as computed by getEmissionDistribution
	@return: The distance between seq1 and seq2
	"""
	pair1, pair2 = items
	seq1, distr1 = pair1
	seq2, distr2 = pair2
	hmm1 = defaultHMMFromDistr(distr1)
	hmm2 = defaultHMMFromDistr(distr2)
	s1_m2 = hmm2.loglikelihood(toSequence(seq1))
	s2_m1 = hmm1.loglikelihood(toSequence(seq2))
	assert not isnan(s1_m2)
	assert not isnan(s2_m1)
	sym = (s1_m2 + s2_m1)/2.0
	return min(-1 * sym, MAX_DIST)

def trainHMM(pair):
	"""
	Given a pair (m: int, S: list of sequences), train a HMM with at
	most m states on S. The HMM is initialized with Smyth's default method,
	then refined with Baum-Welch training.

	@param item: A tuple of the form (m: int, S: list of sequences)
	@return: A tuple (A, B, pi) representing the trained HMM
	"""
	cluster, m = pair
	seqSet = toSequenceSet(cluster)
	hmm = getDefaultHMM(pair)
	hmm.baumWelch(seqSet)
	return hmmToTriple(hmm)

class HMMCluster():
	def __init__(self, S, max_m, min_k, max_k):
		self.S = S
		self.n = len(self.S)
		self.max_m = max_m
		self.min_k = min_k
		self.max_k = max_k
		self.models = {}
		self.pool = Pool()

	def cluster(self):
		"""
		Cluster self.S into self.k clusters, then train a HMM on each cluster.
		Each HMM has a maximum of self.max_m states.
		"""
		print "Generating default HMMs (parallel)..."
		emission_distrs = self.pool.map(getEmissionDistribution,
			[([s], self.max_m) for s in self.S])
		seqmodel_pairs = zip(self.S, emission_distrs)
		print "Done"
		dist_pairs = []
		print "Computing distance matrix (parallel)..."
		for r in xrange(0, self.n):
			for c in xrange(1+r, self.n):
				dist_pairs.append((seqmodel_pairs[r], seqmodel_pairs[c]))
		condensed = self.pool.map(symDistance, dist_pairs)
		dmatrix = squareform(condensed)
		# Get rid of the redundant entries on the lower triangular. For some
		# reason, it doesn't cluster correctly if I don't do this. Doesn't
		# make sense to me.
		for c in xrange(0, self.n):
			for r in xrange(1+c, self.n):
				dmatrix[r][c] = 0
		print "Done"
		print "Hierarchical clustering (serial)..."
		self.linkage_matrix = linkage(dmatrix, method='complete',
			preserve_input=False)
		print "Done"

	def trainModels(self):
		print "Training HMMs on clusters (parallel)..."
		training_items = []
		cluster_sizes = []
		k_values = range(self.min_k, self.max_k+1)
		n_mixtures = len(k_values)
		mixtures = dict(zip(k_values, [([], [])] * n_mixtures))
		# Cut the dendrogram at different k values and prepare the clusters for
		# for HMM in training in parallel. Instead of looping through the k values
		# and training at each one, we "flatten" all of the work items into one list
		# to ensure that all available CPUs are being used.
		for k in k_values:
			labels = fcluster(self.linkage_matrix, k, 'maxclust')
			clusters = partition(self.S, k, labels)
			for cluster in clusters:
				cluster_sizes.append(len(cluster))
				training_items.append((cluster, self.max_m))
		hmm_triples = self.pool.map(trainHMM, training_items)
		idx = 0
		# Reconstruct the mixtures for each k from the list of trained HMMS
		for k in k_values:
			for i in xrange(0, k):
				cluster_size = cluster_sizes[idx]
				hmm_triple = hmm_triples[idx]
				mixtures[k][0].append(hmm_triple)
				mixtures[k][1].append(cluster_size)
				idx += 1
		for k, mixture in mixtures.iteritems():
			self.models[k] = compositeTriple(mixture)
		return self.models

if __name__ == "__main__":
	inpath = sys.argv[1]
	max_m = int(sys.argv[2])
	min_k = int(sys.argv[3])
	max_k = int(sys.argv[4])
	outpath = sys.argv[5]
	if inpath == "-smythex":
		print "Generating synthetic data..."
		sequences = seqSetToList(smyth_example(n=20, length=200))
	else:
		with open(inpath) as datafile:
			print "Loading data..."
			circuits = json.load(datafile)
			sequences = [circ['relays'] for circ in circuits][:100]
	clust = HMMCluster(sequences, max_m, min_k, max_k)
	clust.cluster()
	clust.trainModels()
	with open(outpath, 'w') as outfile:
		pickle.dump(triples, outfile)
