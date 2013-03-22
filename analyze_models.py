from pprint import pprint
import sys, cPickle

if __name__ == "__main__":
	filepath = sys.argv[1]
	with open(filepath) as results_file:
		results = cPickle.load(results_file)
		pprint(results)
