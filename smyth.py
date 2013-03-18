"""
An multithreaded implementation of Smyth 1997's HMM clustering algorithm
for 1-dimensional time series data.
	Syntax: python smyth.py infile target_m min_k max_k outpath
Models for the time series in infile are built and pickled to outpath. target_m,
min_k, and max_k are parameter for the modeling process. See HMMCluster's
documentation for explanations.
@author: Julian Applebaum
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

# These functions really belong as methods of HMMCluster, but we need to leave them
# at the module level for multiprocessing.

def smythEmissionDistribution(pair):
	"""
	Given a pair (S: list of sequences, target_m: int), get the emission
	distribution for Smyth's "default" HMM. target_m is an upper bound on the
	number of states -- if we can only produce m' nonempty clusters,
	then the distribution for a m' state HMM is returned.

	@param pair: A tuple of the form (S: list of sequences, m: int)
	@return: The corresponding emission distribution encoded as a list
			 of (mu, stddev) pairs
	"""
	S, target_m = pair
	combined = flatten([[o] for o in s] for s in S)
	m_prime = min(target_m, len(combined))
	centroids, labels, inertia = k_means(combined, m_prime, init='k-means++')
	clusters = partition(combined, m_prime, labels)
	B = []
	for cluster in clusters:
		if len(cluster) > 0:
			mu = mean(cluster)
			stddev = std(cluster) or EPSILON # The Gaussian is undefined for
			B.append((mu, stddev))			 # standard deviation of 0, which
	return B								 # can happen on uniform data

def smythDefaultTriple(pair):
	"""
	Given a pair (S: list of sequences, target_m: int), initialize a
	HMM triple with at most target_m states using Smyth's "default" method.
	If the observations in S can be clustered into target_m non-empty cluster,
	then the resulting model will have target_m states. Otherwise, the model
	will have one state per non-empty cluster, for however many clusters could
	be created.

	@param pair: A tuple of the form (S: list of sequences, target_m: int)
	@return: The HMM as a (A, B, pi) triple
	"""
	cluster, target_m = pair
	B = smythEmissionDistribution(pair)
	m_prime = len(B)
	A = [[1.0/m_prime] * m_prime] * m_prime
	pi = [1.0/m_prime] * m_prime
	return (A, B, pi)

def randomDefaultTriple(pair):
	pass

def symDistance(items):
	"""
	Calculate Rabiner's symmetrized distance measure between two sequences
	given their corresponding "default" models.

	@param items: A tuple of the form:
					((seq1, triple1), (seq2, triple2))
				  where seq1 and seq2 are singleton lists of emission sequences,
				  and triple1, triple2 are the corresponding HMM triples.
	@return: The distance between seq1 and seq2
	"""
	pair1, pair2 = items
	seq1, triple1 = pair1
	seq2, triple2 = pair2
	hmm1 = tripleToHMM(triple1)
	hmm2 = tripleToHMM(triple2)
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
	hmm = tripleToHMM(smythDefaultTriple(pair))
	hmm.baumWelch(seqSet)
	return hmmToTriple(hmm)

class HMMCluster():
	def __init__(self, S, target_m, min_k, max_k, dist_func='hmm', hmm_init='smyth',
			clust_alg='hierarchical', n_jobs=None):
		"""
		@param S: The sequences to model
		@param target_m: The desired number of components per HMM. The training
			algorithm will attempt to create this many states, but
			it is not guaranteed. See smythDefaultTriple for details.
		@param min_k: The minimum number of mixture components to try
		@param max_k: The maximum number of mixture components to try
		@param hmm_init: Either 'smyth' or 'random'. 'smyth' causes HMMs to
			be initialized with Smyth 1997's "default" method. 'random'
			results in random transition matrices, emission distributions
			and intial state distributions.
		@param clust_alg: Either 'hierarchical' or 'k-medoids'. Specifies
			which clustering algorithm to use.
		@param n_jobs: How many processes to spawn for parallel computations.
			If None, cpu_count() processes are created.
		"""
		self.S = S
		self.n = len(self.S)
		self.target_m = target_m
		self.min_k = min_k
		self.max_k = max_k
		self.models = {}
		self.dist_func = dist_func
		self.hmm_init = hmm_init
		self.clust_alg = clust_alg
		self.training_items = []
		self.partitions = []
		self.k_values = range(self.min_k, self.max_k+1)
		self.pool = Pool(n_jobs)

	def _getHMMDistMatrix(self):
		"""
		Compute the distance matrix using Rabiner's HMM distance measure.
		"""
		print "Generating default HMMs (parallel)..."
		if self.hmm_init == 'smyth':
			init_fn = smythDefaultTriple
		elif self.hmm_init == 'random':
			init_fn = randomDefaultTriple
		init_hmms = self.pool.map(init_fn, (([s], self.target_m) for s in self.S))
		seqmodel_pairs = zip(self.S, init_hmms)
		print "Done"
		dist_pairs = []
		print "Computing distance matrix (parallel)..."
		for r in xrange(0, self.n):
			for c in xrange(1+r, self.n):
				dist_pairs.append((seqmodel_pairs[r], seqmodel_pairs[c]))
		condensed = self.pool.map(symDistance, dist_pairs)
		dist_matrix = squareform(condensed)
		# Get rid of the redundant entries on the lower triangular. For some
		# reason, it doesn't cluster correctly if I don't do this. Doesn't
		# make sense to me.
		for c in xrange(0, self.n):
			for r in xrange(1+c, self.n):
				dist_matrix[r][c] = 0
		print "Done"
		return dist_matrix

	def _getEditDistMatrix(self):
		"""
		Compute the distance matrix using edit distance between sequences.
		"""
		pass

	def _getDistMatrix(self):
		"""
		Compute the distance matrix with a user specified distance function.
		"""
		if self.dist_func == 'hmm':
			return self._getHMMDistMatrix()
		elif self.dist_func == 'editdistance':
			return self._getEditDistMatrix()

	def _hierarchical(self):
		"""
		Create multiple partitions for k values in [self.min_k... self.max_k]
		via hierarchical, agglomerative clustering.
		"""
		dist_matrix = self._getDistMatrix()
		print "Building linkage matrix (serial)..."
		linkage_matrix = linkage(dist_matrix, method='complete',
			preserve_input=False)
		print "Done"
		for k in self.k_values:
			labels = fcluster(linkage_matrix, k, 'maxclust')
			clusters = partition(self.S, k, labels)
			self.partitions.append(clusters)

	def _kMedoids(self):
		"""
		Create multiple partitions for k values in [self.min_k... self.max_k]
		via k-medoids.
		"""
		pass

	def _cluster(self):
		"""
		Create multiple partitions for k values in [self.min_k... self.max_k]
		with a user specified clustering algorithm.
		"""
		if self.clust_alg == 'hierarchical':
			self._hierarchical()
		elif self.clust_alg == 'k-medoids':
			self._kMedoids()

	def _trainModels(self):
		"""
		Train a HMM mixture on each of the k partitions created by _cluster().
		"""
		training_items = []
		cluster_sizes = []
		# Build a list of mapping items to submit as a bulk job
		for partition in self.partitions:
			for cluster in partition:
				cluster_sizes.append(len(cluster))
				training_items.append((cluster, self.target_m))
		mixtures = dict(zip(self.k_values, (([], []) for k in self.k_values)))
		print "Training HMMs on clusters (parallel)..."
		hmm_triples = self.pool.map(trainHMM, training_items)
		print "Done"
		idx = 0
		# Reconstruct the mixtures for each k from the list of trained HMMS
		for k in self.k_values:
			for i in xrange(0, k):
				cluster_size = cluster_sizes[idx]
				hmm_triple = hmm_triples[idx]
				mixtures[k][0].append(hmm_triple)
				mixtures[k][1].append(cluster_size)
				idx += 1

		for k, mixture in mixtures.iteritems():
			self.models[k] = compositeTriple(mixture)

	def model(self):
		"""
		With the user specified k range, clustering algorithm, HMM intialization,
		and distance function, create a set of HMM mixtures models the sequences
		in self.S. When finished, self.models is populated with a dict mapping
		k values to HMM triples.
		"""
		self._cluster()
		self._trainModels()

if __name__ == "__main__":
	inpath = sys.argv[1]
	target_m = int(sys.argv[2])
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
			sequences = [circ['relays'] for circ in circuits]
	clust = HMMCluster(sequences, target_m, min_k, max_k)
	clust.model()
	with open(outpath, 'w') as outfile:
		pickle.dump(clust.models, outfile)
