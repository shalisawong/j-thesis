"""
Utility functions for creating composite HMMs and converting
back and forth from ghmm instances.
@author Julian Applebaum
"""

from matrix_utils import blockDiagMatrix, uniformMatrix
from sequence_utils import flatten
from ghmm import Float, GaussianDistribution, HMMFromMatrices

def compositeTriple(mixture):
	"""
	Given a pair (models: list of HMM triples, cluster_sizes: list of int)
	Combine a list of HMMs into one composite model with a block
	diagonal transition matrix. Initial transition probabilities are
	weighted by the corresponding cluster sizes.

	@param
	@return: The composite HMM
	"""
	models, cluster_sizes = mixture
	n_seqs = sum(cluster_sizes)
	weights = map(lambda n: 1.0*n/n_seqs, cluster_sizes)
	As = [model[0] for model in models]
	B = flatten(model[1] for model in models)
	pi = []
	for i in xrange(0, len(models)):
		pi_m = models[i][2]
		weight = weights[i]
		pi_weighted = map(lambda p: p*weight, pi_m)
		pi += pi_weighted
	A = blockDiagMatrix(As)
	return (A, B, pi)

def hmmToTriple(hmm):
	"""
	Convert a ghmm.GaussianEmissionHMM into a serializeable triple (A, B, pi).
	We need this because Swig objects aren't pickleable, and objects returned
	for multiprocessing.pool.map need to be.
	@param hmm: The HMM
	@param return: The triple (A, B, pi)
	"""
	cmodel = hmm.cmodel
	A = uniformMatrix(cmodel.N, cmodel.N)
	B = []
	pi = []
	for i in xrange(0, cmodel.N):
		state = cmodel.getState(i)
		pi.append(state.pi)
		B.append((state.getMean(0), state.getStdDev(0)))
		for j in xrange(0, cmodel.N):
			A[i][j] = state.getOutProb(j)
	return (A, B, pi)

def tripleToHMM(triple):
	"""
	Get the ghmm.HMM corresponding to the triple (A, B, pi). If all of the
	distributions in B have standard deviations of 0, we create a
	@param triple: The triple
	@return: The HMM
	"""
	A, B, pi = triple
	return HMMFromMatrices(Float(), GaussianDistribution(None), A, B, pi)
