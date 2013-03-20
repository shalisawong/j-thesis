"""
A parallel implementation of Smyth 1997's HMM clustering algorithm
for 1-dimensional time series data.
	Syntax: python smyth.py infile target_m min_k max_k outpath
Models for the time series in infile are built and pickled to outpath. target_m,
min_k, and max_k are parameters for the modeling process. See HMMCluster's
documentation for explanations.
@author: Julian Applebaum
"""

from ghmm import Float, GaussianDistribution, HMMFromMatrices, SequenceSet
from sklearn.cluster import k_means
from fastcluster import linkage
from Pycluster import kmedoids
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import squareform
from numpy import std, mean, array
from numpy import float as npfloat
from sample_gen import smyth_example
from cluster_utils import partition
from sequence_utils import *
from hmm_utils import compositeTriple, hmmToTriple, tripleToHMM
from matrix_utils import uniformMatrix
from pprint import pprint
from math import isnan
from multiprocessing import Pool
import sys, json, pickle

EPSILON = .00001
MAX_DIST = 10**9

# These functions really belong as methods of HMMCluster, but we need to leave
# them at the module level for multiprocessing.

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
	combined = flatten([o for o in s] for s in S)
	vectorized = [[o] for o in combined]
	m_prime = min(target_m, len(vectorized))
	centroids, labels, inertia = k_means(vectorized, m_prime, init='k-means++')
	clusters = partition(combined, labels)
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
	will have one state per non-empty cluster for however many clusters could
	be created.

	@param pair: A tuple of the form (S: list of sequences, target_m: int)
	@return: The HMM as a (A, B, pi) triple
	"""
	cluster, target_m = pair
	B = smythEmissionDistribution(pair)
	m_prime = len(B)
	A = uniformMatrix(m_prime, m_prime, 1.0/m_prime)
	pi = [1.0/m_prime] * m_prime
	return (A, B, pi)

def randomDefaultTriple(pair):
	pass

def symDistance(args):
	"""
	Calculate Rabiner's symmetrized distance measure between two sequences
	given their corresponding "default" models.

	@param args: A pair ((seq1, triple1), (seq2, triple2)) where seq1 and
		seq2 are singleton lists of emission sequences, and triple1, triple2
		are the corresponding HMM triples.
	@return: The distance between seq1 and seq2
	"""
	pair1, pair2 = args
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

def reestimated(pair):
	"""
	Perform Baum-Welch reestimation on a HMM triple with the sequences in S.
	the result.
	@param pair: a tuple (triple, S)
	@return: the reestimated triple
	"""
	triple, S = pair
	seqSet = toSequenceSet(S)
	hmm = tripleToHMM(triple)
	hmm.baumWelch(seqSet)
	return hmmToTriple(hmm)

def trainHMM(pair):
	"""
	Given a pair (m: int, S: list of sequences), train a HMM with at
	most m states on S. The HMM is initialized with Smyth's default method,
	then refined with Baum-Welch training.

	@param item: A tuple (m: int, S: list of sequences)
	@return: A triple (A, B, pi) representing the trained HMM
	"""
	cluster, m = pair
	return reestimated((smythDefaultTriple(pair), cluster))

def kMedoids(args):
	"""
	Do k-medoids clustering on a distance matrix.
	@param args: A tuple of the form (dist_matrix, k, n_passes)
	@return: The result tuple returned by Pycluster.kmedoids
	"""
	dist_matrix, k, n_passes = args
	return kmedoids(dist_matrix, k, n_passes)

class HMMCluster():
	def __init__(self, S, target_m, min_k, max_k, dist_func='hmm',
			hmm_init='smyth', clust_alg='hierarchical', train_mode='blockdiag',
			n_jobs=None):
		"""
		@param S: The sequences to model
		@param target_m: The desired number of components per HMM. The training
			algorithm will attempt to create this many states, but
			it is not guaranteed. See smythDefaultTriple for details.
		@param min_k: The minimum number of mixture components to try
		@param max_k: The maximum number of mixture components to try
		@param dist_func: The distance function to use; either 'hmm' or
			'editdistance'. 'hmm' is Rabiner's symmetrized measure.
		@param hmm_init: Either 'smyth' or 'random'. 'smyth' causes HMMs to
			be initialized with Smyth 1997's "default" method. 'random'
			results in random transition matrices, emission distributions
			and intial state distributions.
		@param clust_alg: Either 'hierarchical' or 'kmedoids'. Specifies
			which clustering algorithm to use.
		@param train_mode: Either 'blockdiag' or 'cluster'. If 'blockdiag',
			we make the block diagonal model and perform Baum-Welch with the
			whole dataset (the way Smyth does). If 'cluster', we train on each
			cluster, then combine into the block diagonal.
		@param n_jobs: How many processes to spawn for parallel computations.
			If None, cpu_count() processes are created.
		"""
		self.S = S
		self.n = len(self.S)
		self.target_m = target_m
		self.min_k = min_k
		self.max_k = max_k
		self.dist_func = dist_func
		self.hmm_init = hmm_init
		self.clust_alg = clust_alg
		self.train_mode = train_mode
		self._sanityCheck()
		self.models = {}
		self.partitions = []
		self.k_values = range(self.min_k, self.max_k+1)
		self.pool = Pool(n_jobs)

	def _sanityCheck(self):
		assert self.min_k <= self.max_k
		assert self.dist_func in ('hmm', 'editdistance')
		assert self.hmm_init in ('smyth', 'random')
		assert self.clust_alg in ('hierarchical', 'kmedoids')
		assert self.train_mode in ('blockdiag', 'cluster')

	def _getHMMDistMatrix(self):
		"""
		Compute the distance matrix using Rabiner's HMM distance measure.
		"""
		print "Generating default HMMs (parallel)...",
		if self.hmm_init == 'smyth':
			init_fn = smythDefaultTriple
		elif self.hmm_init == 'random':
			init_fn = randomDefaultTriple
		init_hmms = self.pool.map(init_fn, (([s], self.target_m) for s in self.S))
		seqmodel_pairs = zip(self.S, init_hmms)
		print "done"
		dist_batch = []
		print "Computing distance matrix (parallel)...",
		for r in xrange(0, self.n):
			for c in xrange(1+r, self.n):
				dist_batch.append((seqmodel_pairs[r], seqmodel_pairs[c]))
		condensed = self.pool.map(symDistance, dist_batch)
		dist_matrix = squareform(condensed)
		# Get rid of the redundant entries on the lower triangular. For some
		# reason, it doesn't cluster correctly if I don't do this. Doesn't
		# make sense to me.
		for c in xrange(0, self.n):
			for r in xrange(1+c, self.n):
				dist_matrix[r][c] = 0
		print "done"
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
		print "Hierachical clustering (serial)...",
		linkage_matrix = linkage(dist_matrix, method='complete',
			preserve_input=False)
		print "done"
		for k in self.k_values:
			labels = fcluster(linkage_matrix, k, 'maxclust')
			clusters = partition(self.S, labels)
			self.partitions.append(clusters)

	def _kMedoids(self):
		"""
		Create multiple partitions for k values in [self.min_k... self.max_k]
		via k-medoids.
		"""
		dist_matrix = self._getDistMatrix()
		batch_items = ((dist_matrix, k, 10) for k in self.k_values)
		print "K-medoids clustering (parallel)...",
		results = self.pool.map(kMedoids, batch_items)
		print "done"
		for i in xrange(0, len(self.k_values)):
			k, result = self.k_values[i], results[i]
			labels, error, nfound = result
			clusters = partition(self.S, labels)
			self.partitions.append(clusters)

	def _cluster(self):
		"""
		Create multiple partitions for k values in [self.min_k... self.max_k]
		with a user specified clustering algorithm.
		"""
		if self.clust_alg == 'hierarchical':
			self._hierarchical()
		elif self.clust_alg == 'kmedoids':
			self._kMedoids()

	def _trainModelsSeparate(self):
		"""
		Train a HMM mixture on each of the k-partitions by separately training
		an HMM on each cluster.
		"""
		batch_items = []
		cluster_sizes = []
		# Build a list of mapping items to submit as a bulk job
		for partition in self.partitions:
			for cluster in partition:
				cluster_sizes.append(len(cluster))
				batch_items.append((cluster, self.target_m))
		mixtures = dict(zip(self.k_values, (([], []) for k in self.k_values)))
		print "Training HMMs on clusters (parallel)...",
		hmm_triples = self.pool.map(trainHMM, batch_items)
		print "done"
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

	def _trainModelsBlockDiag(self):
		"""
		Train a HMM mixture on each of the k-partitions by training one
		HMM on the whole dataset.
		"""
		batch_items = []
		for partition in self.partitions:
			triples = []
			cluster_sizes = []
			for cluster in partition:
				triples.append(smythDefaultTriple((cluster, self.target_m)))
				cluster_sizes.append(len(cluster))
			composite = compositeTriple((triples, cluster_sizes))
			batch_items.append((composite, self.S))
		print "Training composite HMMs on dataset (parallel)...",
		trained_mixtures = self.pool.map(reestimated, batch_items)
		self.models = dict(zip(self.k_values, trained_mixtures))
		print "done"

	def model(self):
		"""
		With the user specified k range, clustering algorithm, HMM intialization,
		and distance function, create a set of HMM mixtures modeling the
		sequences in self.S. When finished, self.models is populated with a
		dict mapping k values to HMM triples.
		"""
		self._cluster()
		if self.train_mode == 'blockdiag':
			self._trainModelsBlockDiag()
		elif self.train_mode == 'cluster':
			self._trainModelsSeparate()

if __name__ == "__main__":
	inpath = sys.argv[1]
	target_m = int(sys.argv[2])
	min_k = int(sys.argv[3])
	max_k = int(sys.argv[4])
	dist_func = sys.argv[5]
	hmm_init = sys.argv[6]
	clust_alg = sys.argv[7]
	outpath = sys.argv[8]
	if inpath == "-smythex":
		print "Generating synthetic data...",
		sequences = seqSetToList(smyth_example(n=20, length=200))
		print "done"
	else:
		with open(inpath) as datafile:
			print "Loading data..."
			circuits = json.load(datafile)
			sequences = [circ['relays'] for circ in circuits]
	clust = HMMCluster(sequences, target_m, min_k, max_k, dist_func,
		hmm_init, clust_alg)
	clust.model()
	for model in clust.models.itervalues():
		print tripleToHMM(model)
	with open(outpath, 'w') as outfile:
		pickle.dump(clust.models, outfile)
