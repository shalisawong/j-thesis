from pprint import pprint
from hmm_utils import tripleToHMM
import sys, cPickle

if __name__ == "__main__":
	filepath = sys.argv[1]
	with open(filepath) as results_file:
		trials = cPickle.load(results_file)
		trial = trials[0]
		model = trial['models'][2]
		pprint(model['hmm_triples'])
		print model['cluster_sizes']
