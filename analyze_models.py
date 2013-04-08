from pprint import pprint
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet
from random import shuffle, seed
import matplotlib.pyplot as plt
import sys, cPickle

if __name__ == "__main__":
	results_path = sys.argv[1]
	k = int(sys.argv[2])
	with open(results_path) as results_file:
		trial = cPickle.load(results_file)
		print trial['rand_seed']
		pprint(trial['times'])
		model = trial['components'][k]
		print "**** Models ****"
		for triple in model['hmm_triples']:
			print tripleToHMM(triple)
		print "**** Cluster sizes ****"
		print model['cluster_sizes']

