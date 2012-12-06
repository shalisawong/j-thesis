from ghmm import *
from sklearn.cluster import Ward
from numpy import std, mean
from pprint import pprint
from math import exp

def getDefaultHMM(s, m, sigma):
	stddev = std(s)
	mu = mean(s)
	A = [[1.0/m] * m] * m
	B = [(mu, stddev)] * m
	distr = GaussianDistribution(None)
	distr.set((mu, stddev))
	pi = [1.0/m] * m
	return HMMFromMatrices(sigma, distr, A, B, pi)

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
	pprint(pi)
	pprint(A)
	pprint(B)

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

def hmmCluster(S, m):
	hmms = [getDefaultHMM(s, m, Float()) for s in S]
	print compositeHMM(hmms, [.333, .333, .333])
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

	return dmatrix


seqs = SequenceSet(Float(), [EmissionSequence(Float(), [1, 2, 3, 5, 6, 7, 9]),
							 EmissionSequence(Float(), [5, 19, 4, 9, 4, 12, 9]),
							 EmissionSequence(Float(), [1, 2, 3, 7, 6, 9, 9])])
pprint(hmmCluster(seqs, 2))


