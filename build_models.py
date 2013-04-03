from smyth import HMMCluster
from numpy import std, mean
from random import shuffle, seed
from math import log
import sys, cPickle, logging, cProfile

MIN_K = 5
MAX_K = 5
MIN_M = 4
MAX_M = 4
BETA = .02
N_TRIALS = 1

def log_series(series):
	return map(lambda o: log(1+o), series)

if __name__ == "__main__":
	logging.disable('warning')
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
		for target_m in xrange(MIN_M, MAX_M+1):
			print "## Target m = %i ##" % target_m
			for i in xrange(0, N_TRIALS):
				print "** Trial %i of %i **" % (i+1, N_TRIALS)
				seed(i)
				shuffle(records)
				out_series = (record['relays_out'] for record in records)
				log_series = map(log_series, out_series)
				max_o = 0
				train_set = log_series[:int(BETA*len(records))]
				for series in log_series:
					max_o = max(max_o, max(series))
				print max_o
				# exit()
				print "Training on %i time series" % len(train_set)
				smyth_out = HMMCluster(train_set, target_m, MIN_K, MAX_K, 'hmm',
					'smyth', 'hierarchical', 'cluster')
				smyth_out.model()
				trial = {
					'components': smyth_out.components,
					'composites': smyth_out.composites,
					'init_hmms': smyth_out.init_hmms,
					'dist_matrix': smyth_out.dist_matrix,
					'times': smyth_out.times,
					'labelings': smyth_out.labelings,
					'randseed': i,
					'beta': BETA,
					'min_k': MIN_K,
					'max_k': MAX_K,
					'target_m': target_m
				}
				outpath = outdir + "/smyth_out_m%i_trial%i.pickle" % (target_m, i)
				with open(outpath, 'w') as outfile:
					cPickle.dump(trial, outfile)
