from random import shuffle
import sys, json

filepath = sys.argv[1]
sample_size = int(sys.argv[2])
n_samples = int(sys.argv[3])
outdir = sys.argv[4]
filename = filepath.split("/")[-1].replace(".json", "")

with open(filepath) as data_file:
	print "Reading data..."
	circuits = json.load(data_file)
	for i in xrange(0, n_samples):
		shuffle(circuits)
		outpath = "%s/%s-RAND%i.json" % (outdir, filename, i)
		sample = circuits[:sample_size]
		print "Writing sample %i" % i
		with open(outpath, 'w') as outfile:
			json.dump(sample, outfile)

