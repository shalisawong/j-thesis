from ghmm import Float, SequenceSet, EmissionSequence

def sequenceEq(s1, s2):
	"""True if s1 = s2, false otherwise"""
	for i in range(0, len(s1)):
		if s1[i] != s2[i]: return False

	return True

def singleton(s):
	"""Create a singleton seqence set"""
	return SequenceSet(Float(), [s])

def toSequenceSet(S):
	return SequenceSet(Float(), list(S))

def toSequence(S):
	return EmissionSequence(Float(), list(S))

def clustersToLists(sequenceSet):
	clusters = []
	for seqSet in sequenceSet:
		cluster = []
		for seq in seqSet:
			cluster.append({'relays': list(seq), 'ident': None})
		clusters.append(cluster)

	return clusters

def seqSetToList(sequenceSet):
	seqs = []
	for seq in sequenceSet:
		seqs.append(list(seq))
	return seqs

def flattenedClusters(sequenceSet):
	clusters = clustersToLists(sequenceSet)
	flattened = []
	for clust in clusters:
		for seq in clust:
			flattened.append(seq)
	return flattened
