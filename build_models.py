'''
 Syntax: python build_models.py cfg_path
'''

from sklearn.cross_validation import train_test_split
from numpy import std, mean
from smyth import HMMCluster
from sequence_utils import trim_inactive
from math import log
from traceback import print_exc
from pprint import pprint
from os.path import isfile
import sys, cPickle, logging, json

def log_series(series):
	return map(lambda o: log(1+o), series)

def preprocess(series):
	return map(lambda s: log_series(trim_inactive(s)), series)

def filter_criteria(series):
	return len(series) > 0 and std(series) > 0

def filter_processed(series):
	return filter(filter_criteria, series)

if __name__ == "__main__":
	logging.disable('warning')
	cfg_path = sys.argv[1]                        
	with open(cfg_path) as cfg_file:
		cfg = json.load(cfg_file)
	with open(cfg['inpath']) as datafile:
		records = cPickle.load(datafile)['records']
	out_series = [record['relays_out'] for record in records]
	# log transformation and trim inactive
	preprocessed = preprocess(out_series)
	filtered = filter_processed(preprocessed)
	print "%i series after preprocessing" % len(filtered)
	for trial_num in xrange(0, cfg['n_trials']):
		rand_seed = cfg['first_seed'] + trial_num
		print "** Trial %i of %i **" % (trial_num+1, cfg['n_trials'])
		for target_m in xrange(cfg['min_m'], cfg['max_m']+1):
			outpath = cfg['outdir'] + ("/smyth_out_m%i_seed_%i.pickle" %
				(target_m, rand_seed))
			if not isfile(outpath):
				print "## Target m = %i ##" % target_m
				if cfg['beta'] < 1:
					train, test = train_test_split(filtered,
						train_size=cfg['beta'], random_state=rand_seed)
				else:
					train = filtered
				print "Training on %i time series" % len(train)
				smyth_out = HMMCluster(train, target_m, cfg['min_k'],
					cfg['max_k'], 'hmm', 'smyth', 'hierarchical', cfg['n_jobs'])
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
					'beta': cfg['beta'],
					'min_k': cfg['min_k'],
					'max_k': cfg['max_k'],
					'target_m': target_m
				}
				with open(outpath, 'w') as outfile:
					print "Dumping results to %s" % outpath
					cPickle.dump(trial, outfile)
			else:
				print "*** Results file %s already exists!" % outpath
