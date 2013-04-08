"""
Compare a raw Tor log to the corresponding one produced by loghacktor.py.
Verify that all timing info is the same, circuit ids are identical, and
anonymized ip addresses have been mapped in a consistent manner.
"""

import autotor
import sys

log_orig = autotor.MultiLogFile(sys.argv[1])
log_ht = autotor.MultiLogFile(sys.argv[2])

assert len(log_orig.circs) == len(log_ht.circs)
ip_map = {}

# For each circuit, first check that everything aside from the IP addresses
# is identical. Then, check that the anonymized IP addresses remain consistent.
for k in log_orig.circs.keys():
	assert k in log_orig.circs
	assert k in log_ht.circs
	e5circ, e5htcirc = log_orig.circs[k], log_ht.circs[k]
	assert e5circ['times'] == e5htcirc['times']
	assert e5circ['src_circ'] == e5htcirc['src_circ']
	assert e5circ['src_circ'] == e5htcirc['src_circ']

	orig_src, orig_dst = e5circ['src_addr'], e5circ['dst_addr']

	if orig_src not in ip_map:
		ip_map[orig_src] = e5htcirc['src_addr']
	else:
		assert ip_map[orig_src] == e5htcirc['src_addr']

	if orig_dst not in ip_map:
		ip_map[orig_dst] = e5htcirc['dst_addr']
	else:
		assert ip_map[orig_dst] == e5htcirc['dst_addr']


# cell rate: 152981 cells/second
# data rate: 74399 KB/s
# total time: 8 seconds
