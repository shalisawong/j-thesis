from sklearn.cross_validation import train_test_split
from build_models import preprocess, filter_processed
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet
from multiprocessing import Pool
import sys, cPickle, glob

def getLikelihood(args):
	k, target_m, triple, test = args
	hmm = tripleToHMM(triple)
	likelihood = hmm.loglikelihood(toSequenceSet(test))
	return (k, target_m, likelihood)

if __name__ == "__main__":
	results_dir = sys.argv[1]
	records_path = sys.argv[2]
	outpath = sys.argv[3]
	agg_results = []
	for filepath in glob.glob("%s/*.pickle" % results_dir):
		with open(filepath) as results_file:
			results = cPickle.load(results_file)
			agg_results.append(results)
	with open(records_path) as records_file:
		records = cPickle.load(records_file)['records']
		out_series = [record['relays_out'] for record in records]
		processed = preprocess(out_series)
		filtered = filter_processed(processed)
		pool = Pool()
		for result in agg_results:
			rand_seed = result['rand_seed']
			beta = result['beta']
			target_m = result['target_m']
			train, test = train_test_split(filtered, train_size=beta,
				random_state=rand_seed)
			batch_items = []
			for k, comp in result['components'].iteritems():
				triple = compositeTriple(comp)
				batch_items.append((k, target_m, triple, list(test)))
			likelihoods = map(getLikelihood, batch_items)
			for k, target_m, likelihood in likelihoods:
				print "k=%i, m=%i, %f" % (k, target_m, likelihood)

