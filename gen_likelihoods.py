import sys, cPickle, glob
from random import sample, seed
from build_models import preprocess, filter_processed
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet

if __name__ == "__main__":
	results_dir = sys.argv[1]
	records_path = sys.argv[2]
	outpath = sys.argv[3]
	agg_results = []
	test_sets = {}
	for filepath in glob.glob("%s/*.pickle" % results_dir):
		with open(filepath) as results_file:
			results = cPickle.load(results_file)
			agg_results.append(results)
	with open(records_path) as records_file:
		records = cPickle.load(records_file)['records']
		out_series = [record['relays_out'] for record in records]
		processed = preprocess(out_series)
		filtered = filter_processed(processed)
		for result in agg_results:
			rand_seed = result['randseed']
			beta = result['beta']
			test_set = test_sets.get(rand_seed)
			target_m = result['target_m']
			if test_set is None:
				seed(rand_seed)
				# This is a very slow way to extract the test set, but since I
				# used random.sample() in build_models, all I have to work with
				# is the training set. Don't want to throw away the models I've
				# produced so far.
				train_set = sample(filtered,int(beta*len(filtered)))
				test_set = filter(lambda s: s not in train_set, filtered)
				test_sets[rand_seed] = test_set
			for k, comp in result['components'].iteritems():
				hmm = tripleToHMM(compositeTriple(comp))
				print hmm.loglikelihood(toSequenceSet(test_set))

