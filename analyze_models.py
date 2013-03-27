from pprint import pprint
from hmm_utils import tripleToHMM
import sys, cPickle

if __name__ == "__main__":
	filepath = sys.argv[1]
	with open(filepath) as results_file:
		results = cPickle.load(results_file)
		for k, hmm in results['models'].iteritems():
			print tripleToHMM(hmm)
