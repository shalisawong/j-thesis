'''
 Syntax: python build_models.py cfg_path
'''

from sklearn.cross_validation import train_test_split
from numpy import std, mean, asarray
from smyth import HMMCluster
from sequence_utils import trim_inactive
from math import log
from traceback import print_exc
from pprint import pprint
from os.path import isfile, isdir
from os import mkdir
import sys, cPickle, logging, json, arff, subprocess

def log_series(series):
	return ([log(1+o) for o in series[0]], series[1])

def log_series_preprocess(series):
	return map(lambda o: log(1+o), series)

def preprocess(series):
	return map(lambda s: log_series(trim_inactive(s)), series)

def filter_criteria(series):
	return len(series[0]) > 0 and std(series[0]) > 0

def filter_criteria_preprocess(series):
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
	# out_series = [([time_series], ip_addr)]
	out_series = [(record['relays_out'], record['ident'][1]) for record in records]
	# log transformation and trim inactive
	preprocessed = preprocess(out_series)
	filtered = filter_processed(preprocessed)
	print "%i series after preprocessing" % len(filtered)
	if not isdir(cfg['outdir']):
		mkdir(cfg['outdir'])
	for trial_num in xrange(0, cfg['n_trials']):
		rand_seed = cfg['first_seed'] + trial_num
		print "** Trial %i of %i **" % (trial_num+1, cfg['n_trials'])
		for target_m in xrange(cfg['min_m'], cfg['max_m']+1):
			outpath = cfg['outdir'] + ("/smyth_out_m%i_seed_%i.pickle" %
				(target_m, rand_seed))
			if not isfile(outpath):
				print "## Target m = %i ##" % target_m
				if cfg['beta'] < 1:
					train_array, test = train_test_split(filtered,
						train_size=cfg['beta'], random_state=rand_seed)
					train = [(series[0],series[1])for series in train_array]
				else:
					train = filtered
				print "Training on %i time series" % len(train)

				# padding to longest length series with -99s
				#print train
				train_len = len(train)
				max_seq_len = len(max((i[0] for i in train), key=len))
				arff_train = []
				padded_train = []
				for i in train:
					pad = (i[0] + [-99.0] * max_seq_len)[:max_seq_len]
					arff_train.append(pad)
					padded_train.append([pad,i[1]])

				arff_out = cfg['arffpath']
				arff.dump(arff_out, arff_train, relation="cellCounts")

				# hand it off to runClustering.java to get clusters
				p = subprocess.Popen("java clustering/runClustering", 
						shell = True,
						stdout=subprocess.PIPE)
				output, errors = p.communicate()
				if p.poll() != 0:
					print "Java subprocess failed"
					break

				labelings = {}
				cluster_out = cfg['cluster_outpath']
				with open(cluster_out) as c_file:
					c_json = json.load(c_file)
				for k in xrange(cfg['min_k'], cfg['max_k']+1):
					labelings[k] = asarray(c_json[str(k).encode('utf-8')])

				smyth_out = HMMCluster(padded_train, target_m, cfg['min_k'],
					cfg['max_k'], labelings, 'hmm', 'smyth', cfg['n_jobs'])
				"""
				try:
					smyth_out.model()
				except Exception, e:
					print "!!!", e, "(trial #%i, target_m=%i)" % \
						(trial_num, target_m)
					print_exc()
					continue
				"""
				smyth_out.model()
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
