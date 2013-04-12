from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import seqSetToList
from cluster_utils import partition
from numpy import histogram
from math import exp
from random import random, randint, seed, sample
from pprint import pprint
from bisect import bisect_left
import sys, cPickle

N = 100
LEN = 100
WINDOW_SIZE = 5000

def idx_chooser(distribution):
	thresholds = reduce(lambda ts, d: ts + [ts[-1]+d], distribution, [0])
	# The last element needs to be 1.0 in order to have a true probability
	# distribution, but floating point errors can leave us with numbers like
	# 0.99999999999999978.
	thresholds[-1] = 1.0
	return lambda: bisect_left(thresholds, random(), hi=len(thresholds)-2)-1

def get_distr(seq_lens):
	"""
	My attempt at sampling from an empirical distribution. This hasn't
	been well tested, so it's currently being used.
	"""
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
	mode = sys.argv[1]
	results_path = sys.argv[2]
	k = int(sys.argv[3])
	out_path = sys.argv[4]
	records = []
	with open(results_path) as resultsfile:
		results = cPickle.load(resultsfile)
	if mode == "-synthetic":
		# model_idx = idx_chooser(mixture['cluster_sizes'])
		mixture = results['components'][k]
		len_distrs = map(get_distr, mixture['seq_lens'])
		records = []
		models = map(tripleToHMM, mixture['hmm_triples'])
		for i, model in enumerate(models):
			sz = mixture['cluster_sizes'][i]
			for j in xrange(0, sz):
				seq_len = len_distrs[i]()
				seq = list(model.sampleSingle(LEN, seed=j))
				create = 0
				destroy = LEN*WINDOW_SIZE
				records.append({
					'ident': (i, i),
					'create': create,
					'destroy': destroy,
					'relays_in': [],
					'relays_out': map(lambda o: max(0, exp(o)-1), seq)
				})
	elif mode == "-clusters":
		data_path = sys.argv[5]
		with open(data_path) as data_file:
			orig_records = cPickle.load(data_file)['records']
		labels = results['labelings'][k]
		clusters = partition(orig_records, labels)
		sampled = map(lambda c: sample(c, 100) if len(c) > 100 else c, clusters)
		for i, cluster in enumerate(sampled):
			for record in cluster:
				record['ident'] = (i, i)
				records.append(record)
		for record in records:
			if record['ident'] == (6, 6):
				print len(record['relays_out'])

	output = {
		'window_size': WINDOW_SIZE,
		'records': records
	}
	with open(out_path, 'w') as outfile:
		cPickle.dump(output, outfile, protocol=2)
