from ghmm import HMMFromMatrices, Float, GaussianDistribution
from matrix_utils import blockDiagMatrix, uniformMatrix

def compositeHMM(mixture):
	"""
	Combine hmms into one composite HMM with a block diagonal
	transition matrix. Initial state probabilities are weighted
	by corresponding values in weights.

	@param hmms: A list of ghmm.GaussianEmissionsHMMs
	@return: The composite HMM
	"""
	n_seqs = reduce(lambda p, s: s + p[0], mixture, 0)
	As = map(lambda p: p[0][0])
	B = reduce(lambda p, b: p[1] + b, mixture)

	A = blockDiagMatrix(As)
	return HMMFromMatrices(Float(), GaussianDistribution(None), A, B, pi)

def hmmToTriple(hmm):
	"""
	Convert a ghmm.GaussianEmissionHMM into a serializeable triple (A, B, pi).
	We need this because Swig objects aren't pickleable, and objects returned
	from during multiprocessing.pool.map need to be.
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
	Get the ghmm.GaussianEmissionHMM corresponding to the triple (A, B, pi)
	@param triple: The triple
	@return: The HMM
	"""
	A, B, pi = triple
	return HMMFromMatrices(Float(), GaussianDistribution(None), A, B, pi)
