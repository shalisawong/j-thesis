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
											# standard deviation of 0, which
											# can happen on uniform data
		B.append((mu, stddev))

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

def hmmCluster(S, m, k):
	hmms = [getDefaultHMM(singleton(s), m, Float()) for s in S]
	dmatrix = zeroMatrix(len(S), len(S))
	max_l = float('-inf')

	# compute the symmetrized similarity matrix
	for j in xrange(0, len(S)):
		for i in xrange(0, len(S)):
			si_mj = hmms[j].loglikelihood(S[i])
			sj_mi = hmms[i].loglikelihood(S[j])
			sym = (si_mj + sj_mi)/2.0
			max_l = max(max_l, sym)
			dmatrix[j][i] = sym

	for j in xrange(0, len(S)):
		dmatrix[j] = map(lambda l: max_l - l, dmatrix[j])

	clustering = clusterFromDMatrix(S, k, dmatrix)
	new_hmms = [getDefaultHMM(c, m, Float()) for c in clustering]
	weights = [len(c) for c in clustering]
	composite = compositeHMM(new_hmms, weights)
	composite.baumWelch(S)
	return composite


# seqs = SequenceSet(Float(), [EmissionSequence(Float(), [1, 2, 3, 5, 6, 7, 9]),
#  							 EmissionSequence(Float(), [5, 19, 4, 9, 4, 12, 9]),
#  							 EmissionSequence(Float(), [1, 2, 3, 7, 6, 9, 9])])

hmm = hmmCluster(seqs, 2, 2)
print hmm


