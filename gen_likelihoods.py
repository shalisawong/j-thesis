from sklearn.cross_validation import train_test_split
from build_models import preprocess, filter_processed
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet
from multiprocessing import Pool
import sys, cPickle, glob

def getLikelihood(args):
	k, target_m, triple, rand_seed, test = args
	hmm = tripleToHMM(triple)
	likelihood = hmm.loglikelihood(toSequenceSet(test))
	return (k, target_m, rand_seed, likelihood)

if __name__ == "__main__":
	results_dir = sys.argv[1]
	records_path = sys.argv[2]
	outpath = sys.argv[3]
	agg_results = []
	print "Aggregating result files..."
	for filepath in glob.glob("%s/*.pickle" % results_dir):
		with open(filepath) as results_file:
			print filepath
			results = cPickle.load(results_file)
			agg_results.append(results)
	print "done"
	with open(records_path) as records_file:
		records = cPickle.load(records_file)['records']
		out_series = [record['relays_out'] for record in records]
		processed = preprocess(out_series)
		filtered = filter_processed(processed)
		batch_items = []
		pool = Pool()
		for result in agg_results:
			rand_seed = result['rand_seed']
			beta = result['beta']
			target_m = result['target_m']
			train, test = train_test_split(filtered, train_size=beta,
				random_state=rand_seed)
			for k, comp in result['components'].iteritems():
				triple = compositeTriple(comp)
				batch_items.append((k, target_m, triple, rand_seed, list(test)))
		print "Computing likelihoods (parallel)..."
		likelihoods = pool.map(getLikelihood, batch_items)
		print "done"
		with open(outpath, 'w') as out_file:
			print "Dumping to %s" % outpath
			cPickle.dump(likelihoods, out_file)
