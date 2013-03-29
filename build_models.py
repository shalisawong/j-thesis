from smyth import HMMCluster
from random import shuffle, seed
import sys, cPickle, logging, cProfile

MIN_K = 4
MAX_K = 7
MIN_M = 4
MAX_M = 10
BETA = .5
N_TRIALS = 10

if __name__ == "__main__":
	logging.disable('warning')
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
		for target_m in xrange(MIN_M, MAX_M+1):
			print "## Target m = %i ##" % target_m
			trials = []
			for i in xrange(0, N_TRIALS):
				print "** Trial %i of %i **" % (i+1, N_TRIALS)
				seed(i)
				shuffle(records)
				sample = records[:int(BETA*len(records))]
				out_series = [record['relays_out'] for record in sample]
				smyth_out = HMMCluster(out_series, target_m, MIN_K, MAX_K, 'hmm',
					'smyth', 'hierarchical', 'cluster')
				smyth_out.model()
				trials.append({
					'models': smyth_out.models,
					'init_hmms': smyth_out.init_hmms,
					'times': smyth_out.times,
					'labelings': smyth_out.labelings,
					'randseed': i
				})
			outpath = outdir + "/smyth_out_m%i.pickle" % target_m
			with open(outpath, 'w') as outfile:
				cPickle.dump(trials, outfile)
