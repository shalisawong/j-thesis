from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import seqSetToList
from math import exp
from random import randint
import sys, cPickle

N = 1000
WINDOW_SIZE = 5000

if __name__ == "__main__":
	filepath = sys.argv[1]
	outpath = sys.argv[2]
	k = int(sys.argv[3])
	with open(filepath) as resultsfile:
		results = cPickle.load(resultsfile)
		model = tripleToHMM((results['composites'][k]))
		records = []
		for i in xrange(0, N):
			n_windows = randint(5, 500)
			seq = list(model.sampleSingle(n_windows, seed=i))
			create = 0
			destroy = 5*n_windows
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




