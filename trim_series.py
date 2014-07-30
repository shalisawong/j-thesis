from numpy import std
from sequence_utils import trim_inactive
from build_models import filter_criteria, log_series
import sys, cPickle

if __name__ == "__main__":
	inpath = sys.argv[1]
	goodpath = sys.argv[2]
	rejpath = sys.argv[3]
	good_records = []
	rej_records = []
	with open(inpath) as datafile:
		data = cPickle.load(datafile)
		print data
		window_size = data['window_size']
		records = data['records']
		for record in records:
			trimmed = trim_inactive(record['relays_out'])
			new_rec = {
				'ident': record['ident'],
				'create': record['create'],
				'destroy': record['destroy'],
				'relays_in': None,
				'relays_out': trimmed,
			}
			if filter_criteria(log_series(trimmed)):
				good_records.append(new_rec)
			elif len(trimmed) > 0:
				rej_records.append(new_rec)
	n_gone = len(records) - len(good_records) - len(rej_records)
	print "%i good records" % len(good_records)
	print "%i reject records" % len(rej_records)
	print "%i len 0 after trimming" % n_gone

	with open(goodpath, 'w') as good_file:
		good_out = {
			'window_size': window_size,
			'records': good_records
		}
		cPickle.dump(good_out, good_file)
	with open(rejpath, 'w') as rej_file:
		rej_out = {
			'window_size': window_size,
			'records': rej_records
		}
		cPickle.dump(rej_out, rej_file)


