from smyth import HMMCluster
from random import shuffle
import sys, cPickle

MIN_K = 2
MAX_K = 8
MIN_M = 4
MAX_M = 8

def dump_model(model, outpath):
	with open(outpath, 'w') as outfile:
		cPickle.dump({
			'models': model.models,
			'times': model.times,
			'labelings': model.labelings,
			'target_m': target_m
		}, outfile)

if __name__ == "__main__":
	inpath = sys.argv[1]
	outdir = sys.argv[2]
	with open(inpath) as datafile:
		records = cPickle.load(datafile)['records']
	shuffle(records)
	sample = records[0:5000]
	in_series = [record['relays_in'] for record in sample]
	out_series = [record['relays_out'] for record in sample]
	for target_m in xrange(MIN_M, MAX_M+1):
		print "Smyth Model (outbound)"
		smyth_out = HMMCluster(out_series, target_m, MIN_K, MAX_K, 'hmm',
			'smyth', 'hierarchical', 'cluster')
		smyth_out.model()
		dump_model(smyth_out, outdir + "/smyth_out_m%i.pickle" % target_m)
		print "Smyth Model (inbound)"
		smyth_in = HMMCluster(in_series, target_m, MIN_K, MAX_K, 'hmm',
			'smyth', 'hierarchical', 'cluster')
		smyth_in.model()
		dump_model(smyth_in, outdir + "/smyth_in_m%i.pickle" % target_m)
		# editdist_out = HMMCluster(out_series, target_m, MIN_K, MAX_K,
		# 	'editdistance', 'smyth', 'kmedoids', 'cluster', 16)
		# editdist_out = HMMCluster(in_series, target_m, MIN_K, MAX_K,
		# 	'editdistance', 'smyth', 'kmedoids', 'cluster', 16)
		# print "Edit Distance Model (outbound)"
		# editdist_out.model()
		# dump_model(editfile, "/editdist_out_m%i.pickle" % target_m, 'w')
		# print "Edit Distance Model (inbound)"
		# editdist_in.model()
		# dump_model(editfile, "/editdist_in_m%i.pickle" % target_m, 'w')


