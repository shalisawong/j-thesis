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
		series = [(record['relays'], record['ident'][1]) for record in records]
		processed = preprocess(series)
		filtered = filter_processed(processed)
		out_filt = []

		# grab just the outbound series
		for i in filtered:
			temp_series = []
			for out in i[0]:
				temp_series.append(out[1])
			out_filt.append((temp_series, i[1]))

		batch_items_test = []
		batch_items_train = []
		pool = Pool()
		for result in agg_results:
			rand_seed = result['rand_seed']
			beta = result['beta']
			target_m = result['target_m']
			train_array, test_array = train_test_split(out_filt,
				train_size=beta, random_state=rand_seed)
			train = [series[0] for series in train_array]
			test = [series[0] for series in test_array]
			for k, comp in result['components'].iteritems():
				triple = compositeTriple(comp)
				batch_items_test.append((k, target_m, triple,
					rand_seed, list(train)))

			for k, comp in result['components'].iteritems():
				triple = compositeTriple(comp)
				batch_items_train.append((k, target_m, triple, rand_seed, list(test)))
		print "Computing train likelihoods (parallel)..."
		likelihoodsTrain = pool.map(getLikelihood, batch_items_train)
		print "Computing test likelihoods (parallel)..."
		likelihoodsTest = pool.map(getLikelihood, batch_items_test)
		print likelihoodsTrain
		print likelihoodsTest
		print "done"
		outTrain = outpath + "train"
		outTest = outpath + "test"
		with open(outTrain, 'w') as out_file:
			print "Dumping to %s" % outTrain
			cPickle.dump(likelihoodsTrain, out_file)
		with open(outTest, 'w') as out_file:
			print "Dumping to %s" % outTest
			cPickle.dump(likelihoodsTest, out_file)

