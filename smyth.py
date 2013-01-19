"""
An implementation of Smyth 1997's HMM clustering algorithm. Currently
only supports time series data with 1-dimensional observations.

@author Julian Applebaum
"""

from ghmm import *
from sklearn.cluster import k_means
from numpy import std, mean, array
from numpy import float as npfloat
from scipy.cluster.hierarchy import complete, fcluster
from pprint import pprint
from sample_gen import smyth_example
from matrix_utils import compositeHMM, uniformMatrix

EPSILON = .00001

def getDefaultHMM(S, m, sigma):
	"""
	Initialize a m state HMM with emission domain sigma using
	Smyth's "default" method.
	"""
	A = [[1.0/m] * m] * m
	B = getEmissionDistribution(S, m)
	distr = GaussianDistribution(None)
	pi = [1.0/m] * m
	return HMMFromMatrices(sigma, distr, A, B, pi)

def getEmissionDistribution(S, m):
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
	print vectorized
	centroids, labels, inertia = k_means(vectorized, m)

	clusters = [[] for i in xrange(0, m)]
	for i in xrange(0, len(flattened)):
		clusters[labels[i]].append(flattened[i])

	B = []
	for cluster in clusters:
		mu = mean(cluster)
		stddev = std(cluster) or EPSILON	# The Gaussian is undefined for
		B.append((mu, stddev))				# standard deviation of 0, which
											# can happen on uniform data
	return B

def clusterFromDMatrix(S, k, dmatrix):
	"""
	Given a distance matrix dmatrix, partition the sequences in S into
	k clusters via hierarchical, complete linkage clustering.
	"""
	clustering = complete(dmatrix)
	assignments = fcluster(clustering, k, 'maxclust')
	clusters = [[] for i in range(0, k)]
	for i in range(0, len(assignments)):
		clusters[assignments[i]-1].append(S[i])

	return [SequenceSet(Float(), c) for c in clusters]

def singleton(s):
	"""Create singleton seqence set"""
	return SequenceSet(Float(), [s])

def sequenceEq(s1, s2):
	"""True if s1 = s2, false otherwise"""
	for i in range(0, len(s1)):
		if s1[i] != s2[i]: return False

	return True

def hmmCluster(S, m, k, silent=True):
	"""
	Create a m*k state HMM mixture modeling the sequences in S.
	The HMM is returned as well as the clustering result used for
	the mixture components.
	"""
	N = len(S)
	if not silent: print "Creating initial HMMs... ",
	hmms = [getDefaultHMM(singleton(s), m, Float()) for s in S]
	if not silent: print "done"
	dmatrix = uniformMatrix(len(S), len(S))
	max_l = float('-inf')

	if not silent: print "Computing symmetrized HMM distance matrix... ",
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

	if not silent: print "done"
	if not silent: print "Clustering on HMM distance matrix... ",
	clustering = clusterFromDMatrix(S, k, dmatrix)
	if not silent: print "done"
	if not silent: print "Computing new default HMMs from clusters... ",
	new_hmms = [getDefaultHMM(c, m, Float()) for c in clustering]
	if not silent: print "done"
	weights = [1.0*len(c)/N for c in clustering]
	composite = compositeHMM(new_hmms, weights)
	if not silent: print composite
	if not silent: print "Performing Baum-Welch re-estimation... ",
	composite.baumWelch(S)
	if not silent: print "done"
	return (composite, clustering)

# Run the experiment Smyth details
if __name__ == "__main__":
  	print "Creating sample data... ",
  	S = smyth_example()
  	print "done"
	hmm, clustering = hmmCluster(S, 2, 2)

	for cluster in clustering:
		print "Cluster size:", len(cluster)

	print hmm
