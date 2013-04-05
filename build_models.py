from smyth import HMMCluster
from numpy import std, mean
from random import sample, seed, uniform
from math import log
from traceback import print_exc
from pprint import pprint
import sys, cPickle, logging, cProfile

MIN_K = 5
MAX_K = 5
MIN_M = 4
MAX_M = 4
BETA = .1
N_TRIALS = 1

def floor_noise(series, logged):
	for i in xrange(0, len(logged)):
		if series[i] < 2:
			logged[i] += uniform(0, .2)
	return logged

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
	logged = map(lambda s: log_series(trim_inactive(s)), series)
	return map(lambda s,l: floor_noise(s, l), series, logged)

def filter_processed(series):
	return filter(lambda s: len(s) > 20 and std(s) > 0, series)

if __name__ == "__main__":
	logging.disable('warning')
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
		out_series = [record['relays_out'] for record in records]
		preprocessed = preprocess(out_series)
		filtered = filter_processed(preprocessed)
		print len(filtered)
		for trial_num in xrange(0, N_TRIALS):
			seed(trial_num)
			print "** Trial %i of %i **" % (trial_num+1, N_TRIALS)
			for target_m in xrange(MIN_M, MAX_M+1):
				print "## Target m = %i ##" % target_m
				train_set = sample(filtered, int(BETA*len(filtered)))
				print "Training on %i time series" % len(train_set)
				smyth_out = HMMCluster(train_set, target_m, MIN_K, MAX_K,
					'hmm', 'smyth', 'hierarchical')
				try:
					smyth_out.model()
				except Exception, e:
					print "!!!", e, "(trial #%i, target_m=%i)" % \
						(trial_num, target_m)
					print_exc()
					continue

				trial = {
					'components': smyth_out.components,
					'composites': smyth_out.composites,
					# 'init_hmms': smyth_out.init_hmms,
					# 'dist_matrix': smyth_out.dist_matrix,
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
