from ghmm import GaussianDistribution, Float, SequenceSet, HMMFromMatrices

def make_data(As, Bs, pis, n=20, length=200, seed=0):
	S = SequenceSet(Float(), [])
	for i in xrange(0, len(As)):
		A = As[i]
		B = Bs[i]
		pi = pis[i]
		distr = GaussianDistribution(None)
		hmm = HMMFromMatrices(Float(), distr, A, B, pi, "HMM_%i" % i)
		sample = hmm.sample(n, length, seed)
		S.merge(sample)
	return S

def smyth_example(n=20, length=200, seed=0):
	As = []
	Bs = []
	pis = []
	As.append([[.6, .4],
		   	   [.4, .6]])
	As.append([[.1, .9],
 		   	   [.9, .1]])
 	Bs.append([(0, 1), (3, 1)])
 	Bs.append([(0, 1), (3, 1)])
 	pis.append([.5, .5])
 	pis.append([.5, .5])
 	return make_data(As, Bs, pis, n, length, seed)

def three_hmm(n=20, length=200, seed=0):
 	As = []
	Bs = []
	pis = []
	As.append([[.6, .4],
		   	   [.4, .6]])
	As.append([[.4, .6],
 		   	   [.6, .4]])
	As.append([[.2, .8],
 		   	   [.8, .2]])
 	Bs.append([(0, 1), (3, 1)])
 	Bs.append([(0, 1), (3, 1)])
 	Bs.append([(12, 1), (0, 1)])
 	pis.append([.5, .5])
 	pis.append([.5, .5])
 	pis.append([.5, .5])
 	return make_data(As, Bs, pis, n, length, seed)
