import autotor, loghacktor

exit5log = autotor.MultiLogFile("/home/japplebaum/Thesis/loganalyze/exit5.log")
exit5loght = autotor.MultiLogFile("/home/japplebaum/Thesis/loganalyze/exit5ht.log")

assert len(exit5log.circs) == len(exit5loght.circs)
ip_map = {}

# For each circuit, first check that everything aside from the IP addresses
# is identical. Then, check that the anonymized IP addresses remain consistent.
for k in exit5log.circs.keys():
	assert k in exit5log.circs
	assert k in exit5loght.circs
	e5circ, e5htcirc = exit5log.circs[k], exit5loght.circs[k]
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
