from sklearn.cross_validation import train_test_split
from numpy import std, mean
from smyth import HMMCluster
from math import log
from traceback import print_exc
from pprint import pprint
from os.path import isfile
import sys, cPickle, logging, cProfile

MIN_K = 3
MAX_K = 50
MIN_M = 3
MAX_M = 10
BETA = .5
N_TRIALS = 20

def trim_inactive(series):
	tail = len(series)
	lead_idx = 0
	trail_idx = tail
	found_nonzero = False
	for idx, obs in enumerate(series):
		if obs < 2:
			if trail_idx == tail:
				trail_idx = idx
			if not found_nonzero:
				lead_idx = idx+1
		else:
			trail_idx = tail
			found_nonzero = True
	return series[lead_idx:trail_idx]

def log_series(series):
	return map(lambda o: log(1+o), series)

def preprocess(series):
	return map(lambda s: log_series(trim_inactive(s)), series)

def filter_processed(series):
	return filter(lambda s: len(s) > 1 and std(s) > 0, series)

if __name__ == "__main__":
	logging.disable('warning')
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	first_seed = int(sys.argv[3])
	n_jobs = None
	if len(sys.argv) == 5:
		n_jobs = int(sys.argv)
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
		out_series = [record['relays_out'] for record in records]
		preprocessed = preprocess(out_series)
		filtered = filter_processed(preprocessed)
		print "%i series after preprocessing" % len(filtered)
		for trial_num in xrange(0, N_TRIALS):
			rand_seed = first_seed + trial_num
			print "** Trial %i of %i **" % (trial_num+1, N_TRIALS)
			for target_m in xrange(MIN_M, MAX_M+1):
				outpath = outdir + ("/smyth_out_m%i_seed_%i.pickle" %
					(target_m, rand_seed))
				if not isfile(outpath):
					print "## Target m = %i ##" % target_m
					train, test = train_test_split(filtered, train_size=BETA,
						random_state=rand_seed)
					print "Training on %i time series" % len(train)
					smyth_out = HMMCluster(train, target_m, MIN_K, MAX_K,
						'hmm', 'smyth', 'hierarchical', n_jobs)
					try:
						smyth_out.model()
					except Exception, e:
						print "!!!", e, "(trial #%i, target_m=%i)" % \
							(trial_num, target_m)
						print_exc()
						continue
					trial = {
						'components': smyth_out.components,
						# 'composites': smyth_out.composites,
						# 'init_hmms': smyth_out.init_hmms,
						# 'dist_matrix': smyth_out.dist_matrix,
						'times': smyth_out.times,
						'labelings': smyth_out.labelings,
						'rand_seed': rand_seed,
						'beta': BETA,
						'min_k': MIN_K,
						'max_k': MAX_K,
						'target_m': target_m
					}
					with open(outpath, 'w') as outfile:
						print "Dumping results to %s" % outpath
						cPickle.dump(trial, outfile)
				else:
					print "*** Results file %s already exists!" % outpath
