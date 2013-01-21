from ghmm import HMMFromMatrices, Float, GaussianDistribution
from matrix_utils import blockDiagMatrix, uniformMatrix

def compositeHMM(hmms, weights):
	"""
	Combine hmms into one composite HMM with a block diagonal
	transition matrix. Initial state probabilities are weighted
	by corresponding values in weights.
	"""
	pi = []
	B = []
	As = []
	for k in range(0, len(hmms)):
		hmm = hmms[k]
		weight = weights[k]
		cmodel = hmm.cmodel
		a = uniformMatrix(cmodel.N, cmodel.N)
		for i in xrange(0, cmodel.N):
			state = cmodel.getState(i)
			pi.append(state.pi * weight)
			B.append((state.getMean(0), state.getStdDev(0)))

			for j in xrange(0, cmodel.N):
				a[i][j] = state.getOutProb(j)

		As.append(a)

	A = blockDiagMatrix(As)
	return HMMFromMatrices(Float(), GaussianDistribution(None), A, B, pi)
