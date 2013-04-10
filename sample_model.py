from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import seqSetToList
from numpy import histogram
from math import exp
from random import random, randint, seed
from pprint import pprint
from bisect import bisect_left
import sys, cPickle

N = 3000
WINDOW_SIZE = 5000

def idx_chooser(distribution):
	thresholds = reduce(lambda ts, d: ts + [ts[-1]+d], distribution, [0])
	# The last element needs to be 1.0 in order to have a true probability
	# distribution, but floating point errors can leave us with numbers like
	# 0.99999999999999978.
	thresholds[-1] = 1.0
	return lambda: bisect_left(thresholds, random(), hi=len(thresholds)-2)-1

def get_distr(seq_lens):
	n_bins = 5000
	hist = histogram(seq_lens, bins=n_bins)
	pairs = filter(lambda p: p[0] > 0, zip(*hist))
	bin_counts = map(lambda p: p[0], pairs)
	bin_edges = map(lambda p: p[1], pairs)
	n_seqs = sum(bin_counts)
	distribution = map(lambda c: 1.0*c/n_seqs, bin_counts)
	choose_idx = idx_chooser(distribution)
	def distr():
		idx = choose_idx()
		left_edge, right_edge = bin_edges[idx], bin_edges[idx+1]
		return randint(int(left_edge), int(right_edge))
	return distr

if __name__ == "__main__":
	filepath = sys.argv[1]
	outpath = sys.argv[2]
	k = int(sys.argv[3])
	with open(filepath) as resultsfile:
		results = cPickle.load(resultsfile)
		mixture = results['components'][k]
		models = map(tripleToHMM, mixture['hmm_triples'])
		model_idx = idx_chooser(mixture['cluster_sizes'])
		len_distrs = map(get_distr, mixture['seq_lens'])
		records = []
		for i in xrange(0, N):
			idx = model_idx()
			model = models[idx]
			seq_len = len_distrs[idx]()
			seq = list(model.sampleSingle(seq_len, seed=i))
			create = 0
			destroy = seq_len*WINDOW_SIZE
			records.append({
				'ident': (i, i),
				'create': create,
				'destroy': destroy,
				'relays_in': [],
				'relays_out': map(lambda o: max(0, exp(o)-1), seq)
			})
		output = {
			'window_size': WINDOW_SIZE,
			'records': records
		}
		with open(outpath, 'w') as outfile:
			cPickle.dump(output, outfile)
