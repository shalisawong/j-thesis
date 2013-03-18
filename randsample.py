"""
Take random samples from a circuit time series dataset encoded in infile.
	Syntax: python randsample.py infile sample_size n_samples outdir
Samples are written to outdir as a JSON files in the same format logparse.py
n_samples files are written, each one containing sample_size randomly selected
time series.
@author: Julian Applebaum
"""

from random import shuffle
import sys, json

inpath = sys.argv[1]
sample_size = int(sys.argv[2])
n_samples = int(sys.argv[3])
outdir = sys.argv[4]
filename = inpath.split("/")[-1].replace(".json", "")

with open(inpath) as data_file:
	print "Reading data..."
	circuits = json.load(data_file)
	for i in xrange(0, n_samples):
		shuffle(circuits)
		outpath = "%s/%s-RAND%i.json" % (outdir, filename, i)
		sample = circuits[:sample_size]
		print "Writing sample %i" % i
		with open(outpath, 'w') as outfile:
			json.dump(sample, outfile)

