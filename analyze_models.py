from pprint import pprint
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet
from random import shuffle, seed
import matplotlib.pyplot as plt
import sys, cPickle

if __name__ == "__main__":
	xs = [1, 2, 3, 4]
	ys = [4, 5, 6, 7]
	results_path = sys.argv[1]
	records_path = sys.argv[2]
	k = int(sys.argv[3])
	with open(results_path) as results_file:
		trial = cPickle.load(results_file)
		model = trial['components'][k]
		print "**** Models ****"
		for triple in model['hmm_triples']:
			print tripleToHMM(triple)
		print "**** Cluster sizes ****"
		print model['cluster_sizes']
		# with open(records_path) as records_file:
		# 	print tripleToHMM(records_file['composites'][k])
		# 	records = cPickle.load(records_file)['records']
		# 	beta = trial['beta']
		# 	seed(trial['randseed'])
		# 	shuffle(records)
		# 	out_series = [record['relays_out'] for record in records]
		# 	test_set = out_series[:int(beta*len(records))]
		# 	print "Computing log likelihood"
		# 	# likelihoods = composite.loglikelihoods(toSequenceSet(test_set))
		# 	# pprint(likelihoods)

