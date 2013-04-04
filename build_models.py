from smyth import HMMCluster
from numpy import std, mean
from random import sample, seed
from math import log
import sys, cPickle, logging, cProfile

MIN_K = 4
MAX_K = 20
MIN_M = 4
MAX_M = 6
BETA = .01
N_TRIALS = 2

def log_series(series):
	return map(lambda o: log(1+o), series)

if __name__ == "__main__":
	logging.disable('warning')
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
		out_series = (record['relays_out'] for record in records)
		log_series = map(log_series, out_series)
		for trial_num in xrange(0, N_TRIALS):
			print "** Trial %i of %i **" % (trial_num+1, N_TRIALS)
			for target_m in xrange(MIN_M, MAX_M+1):
				print "## Target m = %i ##" % target_m
				seed(trial_num)
				train_set = sample(log_series, int(BETA*len(records)))
				print "Training on %i time series" % len(train_set)
				smyth_out = HMMCluster(train_set, target_m, MIN_K, MAX_K,
					'hmm', 'smyth', 'hierarchical')
				try:
					smyth_out.model()
				except ValueError, e:
					print "!!!", e, "(trial #%i, target_m=%i)" % \
						(target_m, trial_num)
					continue
				trial = {
					'components': smyth_out.components,
					'composites': smyth_out.composites,
					'init_hmms': smyth_out.init_hmms,
					'dist_matrix': smyth_out.dist_matrix,
					'times': smyth_out.times,
					'labelings': smyth_out.labelings,
					'randseed': trial_num,
					'beta': BETA,
					'min_k': MIN_K,
					'max_k': MAX_K,
					'target_m': target_m
				}
				outpath = outdir + ("/smyth_out_m%i_trial_%i.pickle" %
					(target_m, trial_num))
				with open(outpath, 'w') as outfile:
					cPickle.dump(trial, outfile)
