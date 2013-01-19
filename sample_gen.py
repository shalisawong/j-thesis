from ghmm import GaussianDistribution, Float, SequenceSet, HMMFromMatrices

def smyth_example(seed1=0, seed2=10, n=20):
	A_1 = [[.6, .4],
		   [.4, .6]]
	A_2 = [[.4, .6],
 		   [.6, .4]]
 	B_1 = [(0, 1), (3, 1)]
 	B_2 = [(0, 1), (3, 1)]
 	pi_1 = [.5, .5]
 	pi_2 = [.5, .5]

 	distr = GaussianDistribution(None)
 	HMM_1 = HMMFromMatrices(Float(), distr, A_1, B_1, pi_1, "HMM_1")
  	HMM_2 = HMMFromMatrices(Float(), distr, A_2, B_2, pi_2, "HMM_2")

  	insample_1 = HMM_1.sample(n, 200, seed1)
  	insample_2 = HMM_2.sample(n, 200, seed2)
	S = SequenceSet(Float(), [])
	S.merge(insample_1)
  	S.merge(insample_2)

  	return S
