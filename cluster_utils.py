from ghmm import SequenceSet, Float
from scipy.cluster.hierarchy import complete, fcluster

def clusterFromDMatrix(S, k, dmatrix):
	"""
	Given a distance matrix dmatrix, partition the sequences in S into
	k clusters via hierarchical, complete linkage clustering.
	"""
	clustering = complete(dmatrix)
	assignments = fcluster(clustering, k, 'maxclust')
	clusters = [[] for i in range(0, k)]
	for i in range(0, len(assignments)):
		clusters[assignments[i]-1].append(S[i])

	return [SequenceSet(Float(), c) for c in clusters]
