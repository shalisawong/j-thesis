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

EPSILON = .00001

def getDefaultHMM(S, m, sigma):
	A = [[1.0/m] * m] * m
	B = getEmissionDistribution(S, m)
	distr = GaussianDistribution(None)
	pi = [1.0/m] * m
	return HMMFromMatrices(sigma, distr, A, B, pi)

def getEmissionDistribution(S, m):
	vectorized = []
	for s in S:
		for o in s:
			vectorized.append([o])

	centroids, labels, inertia = k_means(vectorized, m)
	clusters = [[] for i in xrange(0, m)]
	for s in S:
		for i in xrange(0, len(s)):
			clusters[labels[i]].append(s[i])

	B = []
	for cluster in clusters:
		mu = mean(cluster)
		stddev = std(cluster) or EPSILON	# The Gaussian is undefined for
		B.append((mu, stddev))				# standard deviation of 0, which
											# can happen on uniform data
	return B

def compositeHMM(hmms, weights):
	pi = []
	B = []
	As = []
	for k in range(0, len(hmms)):
		hmm = hmms[k]
		weight = weights[k]
		cmodel = hmm.cmodel
		a = zeroMatrix(cmodel.N, cmodel.N)
		for i in xrange(0, cmodel.N):
			state = cmodel.getState(i)
			pi.append(state.pi * weight)
			B.append((state.getMean(0), state.getStdDev(0)))

			for j in xrange(0, cmodel.N):
				a[i][j] = state.getOutProb(j)

		As.append(a)

	A = blockDiagMatrix(As)
	return HMMFromMatrices(Float(), GaussianDistribution(None), A, B, pi)

def zeroMatrix(c, r):
	"""
	Create a c x r matrix filled with 0's
	"""
	matrix = []
	for i in range(0, r):
		matrix.append([0]*c)
	return matrix

def blockDiagMatrix(matrices):
	"""
	Given matrices A_1, A_2, ... A_n, create the matrix:

	A_1	  ...	    0
	.	A_2			.
	.		... 	.
	. 				.

	0	  	  ... A_n
	"""
	ydim = 0
	xdim = 0

	for matrix in matrices:
		ydim += len(matrix)
		xdim += len(matrix[0])

	block_diag = zeroMatrix(xdim, ydim)
	x_offset = 0
	y_offset = 0

	for matrix in matrices:
		ydim_m = len(matrix)
		xdim_m = len(matrix[0])
		for y in range(0, ydim_m,):
			for x in range(0, xdim_m):
				block_diag[y+y_offset][x+x_offset] = matrix[y][x]

		x_offset += xdim_m
		y_offset += ydim_m

	return block_diag

def clusterFromDMatrix(S, k, dmatrix):
	clustering = complete(array(dmatrix, npfloat))
	assignments = fcluster(clustering, k, 'maxclust')
	clusters = [[] for i in range(0, k)]
	for i in range(0, len(assignments)):
		clusters[assignments[i]-1].append(S[i])

	return [SequenceSet(Float(), c) for c in clusters]

def singleton(s):
	return SequenceSet(Float(), [s])

def sequenceEq(s1, s2):
	for i in range(0, len(s1)):
		if s1[i] != s2[i]: return False

	return True

def hmmCluster(S, m, k):
	N = len(S)
	print "Creating initial HMMs... ",
	hmms = [getDefaultHMM(singleton(s), m, Float()) for s in S]
	print "done"
	dmatrix = zeroMatrix(len(S), len(S))
	max_l = float('-inf')

	print "Computing HMM distance matrix... ",
	# compute the symmetrized dissimilarity matrix
	for j in xrange(0, N):
		for i in xrange(0, N):
			si_mj = hmms[j].loglikelihood(S[i])
			sj_mi = hmms[i].loglikelihood(S[j])
			sym = (si_mj + sj_mi)/2.0
			max_l = max(max_l, sym)
			dmatrix[j][i] = -1 * sym

	print "done"
	print "Clustering on HMM distance matrix... ",
	clustering = clusterFromDMatrix(S, k, dmatrix)
	print "done"
	print "Computing new default HMMs from clusters... ",
	new_hmms = [getDefaultHMM(c, m, Float()) for c in clustering]
	print "done"
	weights = [1.0*len(c)/N for c in clustering]
	composite = compositeHMM(new_hmms, weights)
	#print composite
	print "Performing Baum-Welch re-estimation... ",
	composite.baumWelch(S)
	print "done"
	return (composite, clustering)

if __name__ == "__main__":
	A_1 = [[.6, .4],
		   [.4, .6]]
	A_2 = [[.4, .6],
 		   [.6, .4]]
 	B_1 = [(0, 1), (3, 1)]
 	B_2 = [(0, 1), (3, 1)]
 	pi_1 = [.5, .5]
 	pi_2 = [.5, .5]

 	HMM_1 = HMMFromMatrices(Float(), GaussianDistribution(None), A_1, B_1, pi_1, "HMM_1")
  	HMM_2 = HMMFromMatrices(Float(), GaussianDistribution(None), A_2, B_2, pi_2, "HMM_2")

  	print "Creating sample data... ",
  	sample_1 = HMM_1.sample(20, 200, 1)
  	sample_2 = HMM_2.sample(20, 200, 1)
  	S = SequenceSet(Float(), [])
  	S.merge(sample_1)
  	S.merge(sample_2)
  	print "done"

	hmm, clustering = hmmCluster(S, 2, 2)
	n_11 = 0
	for s in sample_1:
		for s_c1 in clustering[0]:
			if sequenceEq(s, s_c1):
				n_11 += 1

	print "******************"
	print "Cluster 1 has %i sequences" % len(clustering[0])
	print "Cluster 2 has %i sequences" % len(clustering[1])
	print "Cluster 1 has %i sequences from HMM 1, %i from HMM 2" % \
		(n_11, len(clustering[0]) - n_11)
	print "Cluster 2 has %i sequences from HMM 1, %i from HMM 2" % \
		(len(sample_1)-n_11, len(clustering[1]) - len(sample_1) + n_11)
	print hmm

