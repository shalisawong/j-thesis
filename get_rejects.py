from build_models import preprocess, trim_inactive, filter_criteria
from numpy import std
from math import isnan
import sys, cPickle

if __name__ == "__main__":
	inpath = sys.argv[1]
	outpath = sys.argv[2]
	with open(inpath) as datafile:
		data = cPickle.load(datafile)
		orig_records = data['records']
		out_series = (record['relays_out'] for record in orig_records)
		preprocessed = preprocess(out_series)
		reject_data = {
			'window_size': data['window_size'],
			'records': []
		}
		for idx, series in enumerate(preprocessed):
			if not filter_criteria(series) and len(series) > 0:
				orig_record = orig_records[idx]
				rej_record = {
					'ident': orig_record['ident'],
					'create': orig_record['create'],
					'destroy': orig_record['destroy'],
					'relays_in': orig_record['relays_in'],
					'relays_out': orig_record['relays_out']
				}
				reject_data['records'].append(rej_record)
		with open(outpath, 'w') as outfile:
			print "Dumping %i rejects to %s" % (len(reject_data['records']),
				outpath)
			cPickle.dump(reject_data, outfile)
