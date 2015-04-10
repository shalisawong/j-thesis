'''
 Syntax: python build_models.py cfg_path
'''

from sklearn.cross_validation import train_test_split
from numpy import std, mean, asarray
from smyth import HMMCluster
from sequence_utils import trim_inactive
from math import log, exp
from traceback import print_exc
from pprint import pprint
from os.path import isfile, isdir
from os import mkdir
import sys, cPickle, logging, json, arff, subprocess, re

def log_series(series):
	return (map(lambda o: (log(1+o[0]), log(1+o[1])), series[0]), series[1])

def rev_log_series(series):
	return (map(lambda o: (int(round(exp(o[0])-1)), 
		int(round(exp(o[1])-1))),series[0]),series[1])

def rev_log_preprocess(series):
	return map(lambda s: rev_log_series(s),series)

def log_series_preprocess(series):
	return map(lambda o: (log(1+o[0]), log(1+o[1])), series)

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
	with open(cfg['gt_path']) as gt_file:
		gt = cPickle.load(gt_file)
	out_series = [(record['relays'], record['ident'][1]) for record in records]
	# log transformation and trim inactive
	preprocessed = preprocess(out_series)
	filtered = filter_processed(preprocessed)
	print "%i series after preprocessing" % len(filtered)
	if not isdir(cfg['outdir']):
		mkdir(cfg['outdir'])
	for trial_num in xrange(0, cfg['n_trials']):
		rand_seed = cfg['first_seed'] + trial_num
		print "** Trial %i of %i **" % (trial_num+1, cfg['n_trials'])


		if cfg['beta'] < 1:
			train_array, test = train_test_split(filtered,
				train_size=cfg['beta'], random_state=rand_seed)
			train = [(series[0],series[1])for series in train_array]
		else:
			train = filtered
		print "Training on %i time series" % len(train)
		# flatten train and figure out attribute
		# names 
		train_len = len(train)
		max_seq_len = len(max((i[0] for i in train), key=len))
		arff_train = []
		attr_names = []
		out_train = []
		ground_truth = []
		# convert train to integer values
		int_train = rev_log_preprocess(train) 
		for i in int_train:
			# pad with -1 - destroy state
			pad = (i[0] + [('-1','-1')] * max_seq_len)[:max_seq_len]
			flat = [count for tup in pad for count in tup]
			arff_train.append(flat)
			ground_truth.append(gt[hex(i[1])[2:]])
		# for real-valued train, 
		for i in train:
			out_series = []
			for out in i[0]:
				out_series.append(out[1])
			out_train.append((out_series, i[1]))

		# Find labels for ground truth
		ip_addresses = {}
		with open(cfg['shadow_path']) as f:
			print "Reading file..."
			n_entries = 0
			print "Mapping Clients and Circuits..."
			for line in f:
				n_entries += 1
				if n_entries % 50000 == 0 and n_entries != 0:
					print "%i entries processed" % n_entries

				# done in the beginning of scallion.log	
				if "Created Host" in line:

					ip = '(([0-9][0-9]?[0-9]?\\.){3}([0-9][0-9]?[0-9]?))'

					# find name and ip address of host
					try:
						name = re.search("'(.+?)'", line).group(1)
						ip_addr = re.search(ip, line).group(0)

					except AttributeError:
						print "'Created Host' found with either no host name or ip address."
						break;

					ip_addresses[ip_addr] = name
				elif "CLIENTLOGGING" in line:
					break;
		gt_clients = [ip_addresses[i] for i in ground_truth]
		web = 0;
		bulk = 1;
		perf50k = 2;
		perf1m = 3;
		perf5m = 4;
		gt_labels = []
		for l in gt_clients:
			if "web" in l:
				gt_labels.append(web)
			elif "bulk" in l:
				gt_labels.append(bulk)
			elif "perfclient50k" in l:
				gt_labels.append(perf50k)
			elif "perfclient1m" in l:
				gt_labels.append(perf1m)
			elif "perfclient5m" in l:
				gt_labels.append(perf5m)
			else:
				print "Not web or bulk client or perf"
		print "\nGround Truth Labels: "
		print gt_labels
		# write out to gt.json
		with open(cfg['gt_outpath'], 'w') as gt_out:
			json.dump({'ground truth':gt_labels},gt_out)

		for n in xrange(max_seq_len):
			attr_names.append(("cellsIn" + str(n), 'INTEGER'))
			attr_names.append(("cellsOut" + str(n), 'INTEGER'))

		arff_obj = {
			'description': 'Inbound and Outbound Cell Counts',
			'relation': 'Cell Counts',
			'attributes': attr_names,
			'data' : arff_train
			}
		arff_out = cfg['arffpath']
		arff.dump(arff_obj, open(arff_out, 'w'))
		
		print "Clustering Algorithm: " + cfg['cluster_alg']
		print "Distance Measure: " + cfg['dist_measure']
		print "Handing it off to runClustering.java..."
		# hand it off to runClustering.java to get clusters
		p = subprocess.Popen(["/usr/bin/java", "-Xmx2g", 
			"clustering/runClustering", cfg_path],
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while p.poll() is None:
			l = p.stdout.readline()
			print l
		print p.stdout.read()
		print "Clustering completed"
		if cfg['beta'] >= 1:
			print "Clustering evaluation complete"
			break

		labelings = {}
		cluster_out = cfg['cluster_outpath']
		with open(cluster_out) as c_file:
			c_json = json.load(c_file)
		for k in xrange(cfg['min_k'], cfg['max_k']+1):
			labelings[k] = asarray(c_json[str(k).encode('utf-8')])
		#print labelings


		for target_m in xrange(cfg['min_m'], cfg['max_m']+1):
			outpath = cfg['outdir'] + ("/smyth_out_m%i_seed_%i.pickle" %
				(target_m, rand_seed))
			if not isfile(outpath):
				print "## Target m = %i ##" % target_m
							#print labelings
				smyth_out = HMMCluster(out_train, target_m, cfg['min_k'],
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
